import os
from unittest.mock import patch

import json

from aws_lambda_powertools.utilities.typing import LambdaContext

from sandbox_main import lambda_handler


@patch.dict(os.environ, {"BASE_URL": "www.example.com/healthcare-worker"})
def test_status_endpoint_is_served_without_main_handler_coupling():
    response = lambda_handler({"resource": "/_status"}, LambdaContext())

    assert response["statusCode"] == 200
    assert '"resourceType": "Bundle"' in response["body"]
    assert '"resourceType": "Status"' in response["body"]


def test_unknown_endpoint_returns_operation_outcome():
    response = lambda_handler({"resource": "/unknown"}, LambdaContext())

    assert response["statusCode"] == 404
    assert '"resourceType": "OperationOutcome"' in response["body"]


@patch("sandbox_main.RequestRouter")
def test_status_endpoint_router_errors_return_operation_outcome(request_router_mock):
    request_router_mock.return_value.handle_event.side_effect = Exception("boom")

    response = lambda_handler({"resource": "/_status"}, LambdaContext())

    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": "error",
            "code": "exception",
            "details": {
                "coding": [{
                    "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "500",
                    "display": "Internal Server Error",
                }]
            },
        }],
    }
