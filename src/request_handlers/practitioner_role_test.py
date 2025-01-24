from typing import Optional

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_practitioner_role import FhirPractitionerRole
from request_handlers.practitioner_role import PractitionerRoleHandler
from request_handlers.practitioner_test import mock_ldap


def assert_valid_ldaps_user_role(response: FhirPractitionerRole):
    assert response.id == "123"
    assert response.practitioner.identifier.value == "uid"
    assert response.active == True
    assert response.specialty[0].coding[0].code == "specialty"


def practitioner_role_get(role_id: Optional[str]) -> FhirPractitionerRole:
    handler = PractitionerRoleHandler()
    handler_response = handler.get(APIGatewayProxyEvent(data={
        "resource": "/PractitionerRole",
        "queryStringParameters": {
            "practitioner.identifier": role_id
        }
    }))
    return handler_response.main_response[0]


def test_worker_handler():
    mock_ldap()
    response = practitioner_role_get("uid")
    assert_valid_ldaps_user_role(response)
