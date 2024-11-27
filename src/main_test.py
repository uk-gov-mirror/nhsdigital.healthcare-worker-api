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


@patch("main.Log")
@patch("main.RequestRouter")
def test_worker_hcw_exception(request_router_mock, log_mock):
    request_router_mock.return_value.handle_event.side_effect = HcwException(500, "Unknown error")

    response = lambda_handler({"resource": EXAMPLE_PATH}, LambdaContext())

    assert response == {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": EXPECTED_HEADERS,
        "body": json.dumps({"error": "Unknown error"}),
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
        "body": json.dumps({"error": "Internal Server Error"}),
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
        "body": json.dumps({"error": "There is no defined handler for the provided endpoint /NotFound"}),
    }
    assert log_mock.cleanup.called
