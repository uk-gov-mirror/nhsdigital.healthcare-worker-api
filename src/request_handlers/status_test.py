from unittest.mock import patch

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from request_handlers.status import StatusHandler

@patch("request_handlers.status.get_connection")
def test_status_handler(_):
    handler = StatusHandler()

    response = handler.get(APIGatewayProxyEvent(data={}))

    assert response.main_response[0].ok is True

def test_status_handler_with_failed_ldap():
    handler = StatusHandler()

    response = handler.get(APIGatewayProxyEvent(data={}))

    assert response.main_response[0].ok is False
