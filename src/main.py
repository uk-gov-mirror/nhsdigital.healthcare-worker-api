"""
Basic hello world app for an initial deployment
"""
import json
import traceback
from datetime import datetime

import jsonpickle
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic.schema import timedelta

from hcw_exception import HcwException
from logs.log import Log
from request_handlers.handlers import RequestRouter

logger = Log("main")


def lambda_handler(event_dict: dict, context: LambdaContext) -> dict:
    """
    Lambda event handler
    :param event_dict: Event info passed to the lambda for this execution
    :param context: General context info for the lambda
    :return: The response to the API gateway, including response body it will forward on
    """
    start_time = datetime.now()
    event = APIGatewayProxyEvent(event_dict)
    logger.save_event_details(event)
    logger.info("New request received")

    response_headers = {"Content-Type": "application/json"}
    try:
        response = RequestRouter().handle_event(event.resource, event)

        full_response = {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": response_headers,
            "body": jsonpickle.encode(response, unpicklable=False),
        }
    except HcwException as e:
        logger.error(str(e))

        full_response = {
            "isBase64Encoded": False,
            "statusCode": e.status_code,
            "headers": response_headers,
            "body": json.dumps({"error": e.return_message})
        }
    except Exception as e:
        logger.error(str(e))
        logger.error(traceback.format_exc())

        full_response = {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": response_headers,
            "body": json.dumps({"error": "Internal Server Error"})
        }

    end_time = datetime.now()
    debug_timing = {"ms": int((end_time - start_time) / timedelta(milliseconds=1))}
    logger.info(f"Sending response after {json.dumps(debug_timing)}")
    Log.cleanup()
    return full_response


def local_start() -> None:
    """
    This is just a helper function for triggering the lambda handler locally without having to provide the event
    and context objects
    """
    lambda_handler({"resource": "/Practitioner"}, LambdaContext())


if __name__ == '__main__':
    local_start()
