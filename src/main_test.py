import json
from unittest.mock import patch

from aws_lambda_powertools.utilities.typing import LambdaContext

from main import lambda_handler


@patch("main.jsonpickle")
@patch("main.handle_event")
def test_worker(event_handler_mock, jsonpickle_mock):
    event_handler_response = {"worker": "details"}
    event_handler_mock.return_value = event_handler_response

    response = lambda_handler({"resource": "/Practitioner"}, LambdaContext())

    jsonpickle_mock.encode.assert_called_with(event_handler_response, unpicklable=False)
    assert response["statusCode"] == 200
    assert response["body"] == jsonpickle_mock.encode.return_value

