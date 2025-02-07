# Copyright 2014, Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#  http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import base64
import json
import gzip
import re
import ast

import boto3

def format_json(message, return_message: dict):
    if (len(message.split("{", 1))) == 1:
        return return_message | { message: message }

    message_json = "{" + message.split("{", 1)[1].replace("}\\n\"", "}")
    return return_message | ast.literal_eval(message_json)


def transform_log_event(log_event, arn, loggrp, filter_name):
    """Transform each log event.

    The default implementation below just extracts the message and appends a newline to it.

    Args:
    log_event (dict): The original log event. Structure is {"id": str, "timestamp": long, "message": str}
    acct: The aws account from where the Cloudwatch event came from
    arn: The ARN of the Kinesis Stream
    loggrp: The Cloudwatch log group name
    logstrm: The Cloudwatch logStream name (not used below)
    filterName: The Cloudwatch Subscription filter for the Stream
    Returns:
    str: The transformed log event.
        In the case below, Splunk event details are set as:
        time = event time for the Cloudwatch Log
        host = ARN of Firehose
        source = filterName (of cloudwatch Log) contatinated with LogGroup Name
        sourcetype is set as -
            aws:cloudtrail if the Log Group name contains CloudTrail
            aws:cloudwatchlogs:vpcflow if the Log Group name contains VPC
            the environment variable contents of SPLUNK_SOURCETYPE for all other cases
    """

    message = log_event['message']
    match = re.search(r'\[(.*?)]', message)
    log_level = match.group(1) if match else ""

    return_message = {
        "time": str(log_event['timestamp']),
        "host": arn,
        "source": f"{filter_name}:{loggrp}",
        "level": log_level
    }
    return_message = format_json(message, return_message)

    return json.dumps(return_message) + '\n'


def process_records(records, arn):
    for r in records:
        data = load_json_gzip_base64(r['data'])
        rec_id = r['recordId']
        # CONTROL_MESSAGE are sent by CWL to check if the subscription is reachable.
        # They do not contain actual data.
        if data['messageType'] == 'CONTROL_MESSAGE':
            yield {
                'result': 'Dropped',
                'recordId': rec_id
            }
        elif data['messageType'] == 'DATA_MESSAGE':
            joined_data = ''.join([transform_log_event(e, arn, data['logGroup'], data['subscriptionFilters'][0]) for e in data['logEvents']])
            data_bytes = joined_data.encode("utf-8")
            encoded_data = base64.b64encode(data_bytes).decode('utf-8')
            yield {
                'data': encoded_data,
                'result': 'Ok',
                'recordId': rec_id
            }
        else:
            yield {
                'result': 'ProcessingFailed',
                'recordId': rec_id
            }


def split_cwl_record(cwl_record):
    """
    Splits one CWL record into two, each containing half the log events.
    Serializes and compreses the data before returning. That data can then be
    re-ingested into the stream, and it'll appear as though they came from CWL
    directly.
    """
    log_events = cwl_record['logEvents']
    mid = len(log_events) // 2
    rec1 = {k: v for k, v in cwl_record.items()}
    rec1['logEvents'] = log_events[:mid]
    rec2 = {k: v for k, v in cwl_record.items()}
    rec2['logEvents'] = log_events[mid:]
    return [gzip.compress(json.dumps(r).encode('utf-8')) for r in [rec1, rec2]]


def put_records_to_firehose_stream(stream_name, records, client, attempts_made, max_attempts):
    failed_records = []
    codes = []
    err_msg = ''
    # if put_record_batch throws for whatever reason, response['xx'] will error out, adding a check for a valid
    # response will prevent this
    response = None
    try:
        response = client.put_record_batch(DeliveryStreamName=stream_name, Records=records)
    except Exception as e:
        failed_records = records
        err_msg = str(e)

    # if there are no failedRecords (put_record_batch succeeded), iterate over the response to gather results
    if not failed_records and response and response['FailedPutCount'] > 0:
        for idx, res in enumerate(response['RequestResponses']):
            # (if the result does not have a key 'ErrorCode' OR if it does and is empty) => we do not need to re-ingest
            if not res.get('ErrorCode'):
                continue

            codes.append(res['ErrorCode'])
            failed_records.append(records[idx])

        err_msg = 'Individual error codes: ' + ','.join(codes)

    if failed_records:
        if attempts_made + 1 < max_attempts:
            print('Some records failed while calling PutRecordBatch to Firehose stream, retrying. %s' % (err_msg))
            put_records_to_firehose_stream(stream_name, failed_records, client, attempts_made + 1, max_attempts)
        else:
            raise RuntimeError('Could not put records after %s attempts. %s' % (str(max_attempts), err_msg))


def put_records_to_kinesis_stream(stream_name, records, client, attempts_made, max_attempts):
    failed_records = []
    codes = []
    err_msg = ''
    # if put_records throws for whatever reason, response['xx'] will error out, adding a check for a valid
    # response will prevent this
    response = None
    try:
        response = client.put_records(StreamName=stream_name, Records=records)
    except Exception as e:
        failed_records = records
        err_msg = str(e)

    # if there are no failedRecords (put_record_batch succeeded), iterate over the response to gather results
    if not failed_records and response and response['FailedRecordCount'] > 0:
        for idx, res in enumerate(response['Records']):
            # (if the result does not have a key 'ErrorCode' OR if it does and is empty) => we do not need to re-ingest
            if not res.get('ErrorCode'):
                continue

            codes.append(res['ErrorCode'])
            failed_records.append(records[idx])

        err_msg = 'Individual error codes: ' + ','.join(codes)

    if failed_records:
        if attempts_made + 1 < max_attempts:
            print('Some records failed while calling PutRecords to Kinesis stream, retrying. %s' % (err_msg))
            put_records_to_kinesis_stream(stream_name, failed_records, client, attempts_made + 1, max_attempts)
        else:
            raise RuntimeError('Could not put records after %s attempts. %s' % (str(max_attempts), err_msg))


def create_reingestion_record(is_sas, original_record, data=None):
    if data is None:
        data = base64.b64decode(original_record['data'])
    r = {'Data': data}
    if is_sas:
        r['PartitionKey'] = original_record['kinesisRecordMetadata']['partitionKey']
    return r


def load_json_gzip_base64(base64_data):
    return json.loads(gzip.decompress(base64.b64decode(base64_data)))


def lambda_handler(event, context):
    is_sas = 'sourceKinesisStreamArn' in event
    stream_arn = event['sourceKinesisStreamArn'] if is_sas else event['deliveryStreamArn']
    region = stream_arn.split(':')[3]
    stream_name = stream_arn.split('/')[1]
    records = list(process_records(event['records'], stream_arn))
    projected_size = 0
    record_lists_to_reingest = []

    for idx, rec in enumerate(records):
        original_record = event['records'][idx]

        if rec['result'] != 'Ok':
            continue

        # If a single record is too large after processing, split the original CWL data into two, each containing half
        # the log events, and re-ingest both of them (note that it is the original data that is re-ingested, not the
        # processed data). If it's not possible to split because there is only one log event, then mark the record as
        # ProcessingFailed, which sends it to error output.
        if len(rec['data']) > 6000000:
            cwl_record = load_json_gzip_base64(original_record['data'])
            if len(cwl_record['logEvents']) > 1:
                rec['result'] = 'Dropped'
                record_lists_to_reingest.append(
                    [create_reingestion_record(is_sas, original_record, data) for data in split_cwl_record(cwl_record)])
            else:
                rec['result'] = 'ProcessingFailed'
                print(('Record %s contains only one log event but is still too large after processing (%d bytes), ' +
                        'marking it as %s') % (rec['recordId'], len(rec['data']), rec['result']))
            del rec['data']
        else:
            projected_size += len(rec['data']) + len(rec['recordId'])
            # 6000000 instead of 6291456 to leave ample headroom for the stuff we didn't account for
            if projected_size > 6000000:
                record_lists_to_reingest.append([create_reingestion_record(is_sas, original_record)])
                del rec['data']
                rec['result'] = 'Dropped'

    # call putRecordBatch/putRecords for each group of up to 500 records to be re-ingested
    if record_lists_to_reingest:
        records_reingested_so_far = 0
        client = boto3.client('kinesis' if is_sas else 'firehose', region_name=region)
        max_batch_size = 500
        flattened_list = [r for sublist in record_lists_to_reingest for r in sublist]
        for i in range(0, len(flattened_list), max_batch_size):
            record_batch = flattened_list[i:i + max_batch_size]
            # last argument is maxAttempts
            args = [stream_name, record_batch, client, 0, 20]
            if is_sas:
                put_records_to_kinesis_stream(*args)
            else:
                put_records_to_firehose_stream(*args)
            records_reingested_so_far += len(record_batch)
            print('Reingested %d/%d' % (records_reingested_so_far, len(flattened_list)))

    print('%d input records, %d returned as Ok or ProcessingFailed, %d split and re-ingested, %d re-ingested as-is' % (
        len(event['records']),
        len([r for r in records if r['result'] != 'Dropped']),
        len([l for l in record_lists_to_reingest if len(l) > 1]),
        len([l for l in record_lists_to_reingest if len(l) == 1])))

    return {'records': records}
