from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from request_handlers.status import StatusHandler


def test_status_handler():
    handler = StatusHandler()

    response = handler.get(APIGatewayProxyEvent(data={}))

    assert response.ok is True
