from typing import Optional
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_worker import FhirWorker
from hcw_exception import HcwException
from ldap.nhs_person import NhsPerson
from request_handlers.worker import PractitionerHandler

import request_handlers.worker


def assert_valid_ldaps_user(response):
    assert response.id == "uid"
    assert response.resourceType == "Practitioner"
    assert response.active

    assert len(response.identifier) == 1
    assert response.identifier[0].system == "https://fhir.nhs.uk/Id/sds-user-id"
    assert response.identifier[0].value == "uid"

    assert len(response.name) == 1
    assert response.name[0].use == "usual"
    assert response.name[0].prefix == "Mr"
    assert response.name[0].family == "Smith"
    assert response.name[0].given == "Bob John James"


def assert_valid_sandbox_user(response):
    assert response.id == 123
    assert response.resourceType == "Practitioner"
    assert response.active

    assert len(response.identifier) == 1
    assert response.identifier[0].system == "https://fhir.nhs.uk/Id/sds-user-id"
    assert response.identifier[0].value == 123

    assert len(response.name) == 1
    assert response.name[0].use == "usual"
    assert response.name[0].prefix == "Mrs"
    assert response.name[0].given == "Tabby Ashlyn"
    assert response.name[0].family == "Westbrook"


def mock_ldap(uid: Optional[str] = "uid", sn: Optional[str] = "Smith",
                given_name: Optional[str] = "Bob", nhs_middle_names=None, title: Optional[str] = "Mr",
                status: Optional[str] = "1"):
    if nhs_middle_names is None:
        nhs_middle_names = ["John", "James"]

    ldap_connection_mock = MagicMock()
    mock_ldap_response = NhsPerson([uid], [sn], [given_name], nhs_middle_names, [title], status)
    ldap_connection_mock.return_value.search_active_nhs_person.return_value = mock_ldap_response
    request_handlers.worker.get_connection = ldap_connection_mock

    return ldap_connection_mock


def practitioner_get(uid: Optional[str]) -> FhirWorker:
    handler = PractitionerHandler()
    return handler.get(APIGatewayProxyEvent(data={
        "resource": "/Practitioner",
        "queryStringParameters": {
            "identifier": uid
        }
    }))


def test_worker_handler():
    mock_ldap()
    response = practitioner_get("uid")
    assert_valid_ldaps_user(response)


def test_missing_id():
    mock_ldap()

    with pytest.raises(HcwException) as e:
        practitioner_get(None)

    assert e.value.status_code == 400
    assert e.value.message == "Missing practitioner identifier"


def test_ldap_returns_error():
    ldap_connection_mock = mock_ldap()
    ldap_connection_mock.return_value.search_active_nhs_person.side_effect = HcwException(500, "LDAP Error")

    with pytest.raises(HcwException) as e:
        practitioner_get("uid")

    assert e.value == ldap_connection_mock.return_value.search_active_nhs_person.side_effect


class TestLdapMissingField:
    """
    These tests check what happens if a field in missing in the ldap response. This often isn't an expected scenario
    since fields like "uid" are expected on all entries. It's still sensible to make sure that we handle these responses
    appropriately.
    """
    def test_ldap_response_with_no_uid(self):
        mock_ldap(uid=None)

        response = practitioner_get("uid")

        assert response.id is None
        assert response.identifier[0].value is None

    def test_ldap_response_with_no_sn(self):
        mock_ldap(sn=None)

        response = practitioner_get("uid")

        assert response.name[0].family is None

    def test_ldap_response_with_no_given_name(self):
        mock_ldap(given_name=None)

        response = practitioner_get("uid")

        # Just middle names
        assert response.name[0].given == "John James"

    def test_ldap_response_with_single_middle_name(self):
        mock_ldap(nhs_middle_names=["Middle"])

        response = practitioner_get("uid")

        assert response.name[0].given == "Bob Middle"

    def test_ldap_response_with_no_middle_name(self):
        mock_ldap(nhs_middle_names=False)

        response = practitioner_get("uid")

        assert response.name[0].given == "Bob"

    def test_ldap_response_with_empty_middle_names(self):
        mock_ldap(nhs_middle_names=[])

        response = practitioner_get("uid")

        assert response.name[0].given == "Bob"

    def test_ldap_response_with_no_first_or_middle_name(self):
        mock_ldap(given_name=None, nhs_middle_names=[])

        response = practitioner_get("uid")

        assert response.name[0].given == ""

    def test_ldap_response_with_no_title(self):
        mock_ldap(title=None)

        response = practitioner_get("uid")

        assert response.name[0].prefix is None
