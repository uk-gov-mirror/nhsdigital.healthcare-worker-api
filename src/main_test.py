import os
import json
from unittest.mock import patch

from aws_lambda_powertools.utilities.typing import LambdaContext

from hcw_exception import HcwException
from main import lambda_handler
from request_handlers.handlers import UnknownHandlerException

EXAMPLE_PATH = "/example"
EXPECTED_HEADERS = {"Content-Type": "application/json"}


@patch("main.Log")
@patch("main.jsonpickle")
@patch("main.RequestRouter")
def test_worker(request_router_mock, jsonpickle_mock, log_mock):
    event_handler_response = {"worker": "details"}
    request_router_mock.return_value.handle_event.return_value = event_handler_response

    response = lambda_handler({"resource": EXAMPLE_PATH}, LambdaContext())

    jsonpickle_mock.encode.assert_called_with(event_handler_response, unpicklable=False)
    assert response["statusCode"] == 200
    assert response["body"] == jsonpickle_mock.encode.return_value
    assert log_mock.cleanup.called


@patch.dict(os.environ, {"SANDBOX_MODE": "true"}, clear=False)
@patch("main.Log")
@patch("main.jsonpickle")
@patch("main.RequestRouter")
def test_worker_sandbox_adds_cors_origin_header(request_router_mock, jsonpickle_mock, log_mock):
    event_handler_response = {"worker": "details"}
    request_router_mock.return_value.handle_event.return_value = event_handler_response

    response = lambda_handler({
        "resource": EXAMPLE_PATH,
        "headers": {
            "Origin": "https://digital.nhs.uk"
        }
    }, LambdaContext())

    assert response["statusCode"] == 200
    assert response["headers"] == {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://digital.nhs.uk",
        "Vary": "Origin"
    }
    assert log_mock.cleanup.called


@patch.dict(os.environ, {"SANDBOX_MODE": "true"}, clear=False)
@patch("main.Log")
@patch("main.jsonpickle")
@patch("main.RequestRouter")
def test_worker_sandbox_adds_credentials_header_when_authorization_present(request_router_mock, jsonpickle_mock, log_mock):
    event_handler_response = {"worker": "details"}
    request_router_mock.return_value.handle_event.return_value = event_handler_response

    response = lambda_handler({
        "resource": EXAMPLE_PATH,
        "headers": {
            "Origin": "https://digital.nhs.uk",
            "Authorization": "Bearer token"
        }
    }, LambdaContext())

    assert response["statusCode"] == 200
    assert response["headers"] == {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://digital.nhs.uk",
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin"
    }
    assert log_mock.cleanup.called


@patch("main.Log")
@patch("main.RequestRouter")
def test_worker_hcw_exception(request_router_mock, log_mock):
    request_router_mock.return_value.handle_event.side_effect = HcwException(500, "Unknown error", "exception")

    response = lambda_handler({"resource": EXAMPLE_PATH}, LambdaContext())

    assert response == {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": EXPECTED_HEADERS,
        "body": json.dumps({
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "exception",
                "details": {
                    "coding": [{
                        "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                        "code": "500",
                        "display": "Unknown error"}]
                }
            }]
        }),
    }
    assert log_mock.cleanup.called


@patch("main.Log")
@patch("main.RequestRouter")
def test_worker_general_exception(request_router_mock, log_mock):
    request_router_mock.return_value.handle_event.side_effect = Exception()

    response = lambda_handler({"resource": EXAMPLE_PATH}, LambdaContext())

    assert response == {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": EXPECTED_HEADERS,
        "body": json.dumps({
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "exception",
                "details": {
                    "coding": [{
                        "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                        "code": "500",
                        "display": "Internal Server Error"}]
                }
            }]
        }),
    }
    assert log_mock.cleanup.called


@patch("main.Log")
@patch("main.RequestRouter")
def test_worker_unknown_endpoint(request_router_mock, log_mock):
    request_router_mock.return_value.handle_event.side_effect = UnknownHandlerException("/NotFound")

    response = lambda_handler({"resource": "/NotFound"}, LambdaContext())

    assert response == {
        "isBase64Encoded": False,
        "statusCode": 404,
        "headers": EXPECTED_HEADERS,
        "body": json.dumps({
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "unknown",
                "details": {
                    "coding": [{
                        "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                        "code": "404",
                        "display": "There is no defined handler for the provided endpoint /NotFound"}]
                }
            }]
        })
    }
    assert log_mock.cleanup.called
