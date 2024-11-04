from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from request_handlers.worker import PractitionerHandler


def test_worker_handler():
    handler = PractitionerHandler()
    response = handler.get(APIGatewayProxyEvent(data={"resource": "/Practitioner"}))

    assert response.id == "111"
