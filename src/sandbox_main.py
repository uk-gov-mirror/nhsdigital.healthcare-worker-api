import json
from datetime import datetime

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic.schema import timedelta

from logs.log import Log
from main import lambda_handler as default_lambda_handler
from request_handlers.sandbox_static_responses import get_sandbox_response

logger = Log("sandbox_main")
STATUS_ENDPOINTS = {"/", "/_status"}


def lambda_handler(event_dict: dict, context: LambdaContext) -> dict:
    start_time = datetime.now()
    event = APIGatewayProxyEvent(event_dict)
    if event.resource in STATUS_ENDPOINTS:
        return default_lambda_handler(event_dict, context)

    sandbox_response = get_sandbox_response(event)

    if sandbox_response:
        status_code, body = sandbox_response
        full_response = {
            "isBase64Encoded": False,
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": body,
        }
        end_time = datetime.now()
        debug_timing = {"ms": int((end_time - start_time) / timedelta(milliseconds=1))}
        logger.info(f"Sending sandbox response after {json.dumps(debug_timing)}", "RESP_SENT_TIME", "null")
        Log.cleanup()
        return full_response

    return {
        "isBase64Encoded": False,
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "unknown",
                "details": {
                    "coding": [{
                        "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                        "code": "404",
                        "display": f"There is no defined handler for the provided endpoint {event.resource}",
                    }]
                },
            }],
        }),
    }