from unittest.mock import patch

from aws_lambda_powertools.utilities.typing import LambdaContext
from urllib3 import request

from main import lambda_handler


@patch("main.requests.get")
def test_worker(get_mock):
    response = lambda_handler({"resource": "/Practitioner"}, LambdaContext())

    assert response["statusCode"] == 200
    url = "http://proxy-in.nhsref-1.auth-ptl.cis2.spineservices.nhs.uk/openam/json/health/live"  # NOSONAR
    get_mock.assert_called_with(url)

