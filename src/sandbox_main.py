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
from request_handlers.sandbox_static_responses import get_sandbox_response

logger = Log("sandbox_main")
STATUS_ENDPOINTS = {"/", "/_status"}


def lambda_handler(event_dict: dict, context: LambdaContext) -> dict:
    start_time = datetime.now()
    event = APIGatewayProxyEvent(event_dict)
    try:
        if event.resource in STATUS_ENDPOINTS:
            response = RequestRouter().handle_event(event.resource, event)
            full_response = _build_response(200, jsonpickle.encode(response, unpicklable=False))
        else:
            sandbox_response = get_sandbox_response(event)

            if sandbox_response:
                status_code, body = sandbox_response
                full_response = _build_response(status_code, body)
            else:
                full_response = _build_response(
                    404,
                    _build_operation_outcome(
                        404,
                        "unknown",
                        f"There is no defined handler for the provided endpoint {event.resource}",
                    ),
                )
    except HcwException as exc:
        logger.error(str(exc), "RESP_ERROR_001", "null")
        full_response = _build_response(
            exc.status_code,
            _build_operation_outcome(exc.status_code, exc.fhir_code, exc.return_message),
        )
    except Exception as exc:
        logger.error(str(exc), "RESP_ERROR_002", "null")
        logger.error(traceback.format_exc(), "RESP_ERROR_003", "null")
        full_response = _build_response(
            500,
            _build_operation_outcome(500, "exception", "Internal Server Error"),
        )

    end_time = datetime.now()
    debug_timing = {"ms": int((end_time - start_time) / timedelta(milliseconds=1))}
    logger.info(f"Sending sandbox response after {json.dumps(debug_timing)}", "RESP_SENT_TIME", "null")
    Log.cleanup()
    return full_response


def _build_response(status_code: int, body: str) -> dict:
    return {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": body,
    }


def _build_operation_outcome(status_code: int, code: str, display: str) -> str:
    return json.dumps({
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": "error",
            "code": code,
            "details": {
                "coding": [{
                    "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": str(status_code),
                    "display": display,
                }]
            },
        }],
    })
