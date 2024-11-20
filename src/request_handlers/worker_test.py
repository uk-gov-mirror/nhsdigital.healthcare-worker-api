from unittest.mock import patch

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.worker import FhirWorker
from ldap.nhs_person import NhsPerson
from request_handlers.worker import PractitionerHandler


@patch("request_handlers.worker.HcwLdapConnection")
def test_worker_handler(ldap_connection_mock):
    mock_ldap_response = NhsPerson(["uid"], ["Smith"], ["Bob"], ["John", "James"],
                                    ["Mr"], "1")
    ldap_connection_mock.return_value.search_active_nhs_person.return_value = mock_ldap_response

    handler = PractitionerHandler()
    response: FhirWorker = handler.get(APIGatewayProxyEvent(data={"resource": "/Practitioner"}))

    assert response.id == "uid"
    assert response.resourceType == "Practitioner"
    assert response.active

    assert len(response.identifier) == 1
    assert response.identifier[0].system == "https://fhir.nhs.uk/Id/sds-user-id"
    assert response.identifier[0].value == "uid"

    assert len(response.name) == 1
    assert response.name[0].use == "usual"
    assert response.name[0].family == "Smith"
    assert response.name[0].given == "Bob John James"
    assert response.name[0].prefix == "Mr"
