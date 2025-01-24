from typing import Optional
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_practitioner import FhirPractitioner
from hcw_exception import HcwException
from ldap.nhs_person import NhsPerson, NhsOrgPersonRole, NhsOrgPerson
from request_handlers.practitioner import PractitionerHandler

import request_handlers.practitioner
import request_handlers.practitioner_role


def assert_valid_ldaps_user(response):
    assert response.id == "uid"
    assert response.resourceType == "Practitioner"
    assert response.active

    assert len(response.identifier) == 10
    assert response.identifier[0].system == "https://fhir.nhs.uk/Id/sds-user-id"
    assert response.identifier[0].value == "uid"
    assert response.identifier[1].system == "https://fhir.nhs.uk/Id/rpsgb-membership-number"
    assert response.identifier[1].value == "rpsgb-number"
    assert response.identifier[2].system == "https://fhir.nhs.uk/Id/gmc-number"
    assert response.identifier[2].value == "gmc-number"
    assert response.identifier[3].system == "https://fhir.nhs.uk/Id/gdp-number"
    assert response.identifier[3].value == "gdp-number"
    assert response.identifier[4].system == "https://fhir.nhs.uk/Id/gdc-number"
    assert response.identifier[4].value == "gdc-number"
    assert response.identifier[5].system == "https://fhir.nhs.uk/Id/rcn-number"
    assert response.identifier[5].value == "rcn-number"
    assert response.identifier[6].system == "https://fhir.nhs.uk/Id/nmc-number"
    assert response.identifier[6].value == "nmc-number"
    assert response.identifier[7].system == "https://fhir.nhs.uk/Id/gmp-number"
    assert response.identifier[7].value == "gmp-number"
    assert response.identifier[8].system == "https://fhir.nhs.uk/Id/consultant-code"
    assert response.identifier[8].value == "consultant-code"
    assert response.identifier[9].system == "https://fhir.nhs.uk/Id/nacs-practitioner-code"
    assert response.identifier[9].value == "nacs-practitioner-code"

    assert len(response.name) == 1
    assert response.name[0].use == "usual"
    assert response.name[0].prefix == ["Mr"]
    assert response.name[0].family == "Smith"
    assert response.name[0].given == ["Bob John James"]

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
                given_name: Optional[str] = "Bob", nhs_middle_names: Optional[str] = "John James",
                title: Optional[str] = "Mr", status: Optional[str] = "1"):
    ldap_connection_mock = MagicMock()
    nhs_person = NhsPerson({
        "uid": uid,
        "sn": sn,
        "givenName": given_name,
        "nhsMiddleNames": nhs_middle_names,
        "personalTitle": title,
        "nhsPersonStatus": status,
        "nhsPrinOcc": "specialty",
        "nhsRPSGB": "rpsgb-number",
        "nhsGMC": "gmc-number",
        "nhsGDP": "gdp-number",
        "nhsGDC": "gdc-number",
        "nhsRCN": "rcn-number",
        "nhsNMC": "nmc-number",
        "nhsGMP": "gmp-number",
        "nhsConsultant": "consultant-code",
        "nhsOcsPrCode": "nacs-practitioner-code"
    })
    org_person_role = NhsOrgPersonRole({
        "uniqueIdentifier": "123",
        "nhsBusinessFunctionsCodes": ["R0001", "R0002"],
        "nhsBusinessFunctions": ["B0001", "B0002"],
        "nhsJobRole": "Job Role",
        "nhsJobRoleCode": "job-role-code",
        "nhsIDCode": "id-code",
        "nhsSiteNames": ["site-1", "site-2"],
        "nhsSiteCodes": ["1", "2"],
        "nhsOpenDate": "20200101",
        "nhsCloseDate": "30000101"
    })
    nhs_org_person = NhsOrgPerson({
        "uniqueIdentifier": "org-person-id",
        "nhsOpenDate": "20000101",
        "nhsIDCode": "id-code",
        "o": "nhs",
    })

    org_person_role.practitioner = nhs_person
    org_person_role.org_person = nhs_org_person

    ldap_connection_mock.return_value.search_active_nhs_person.return_value = [nhs_person, [nhs_org_person], [org_person_role]]
    request_handlers.practitioner.get_connection = ldap_connection_mock
    request_handlers.practitioner_role.get_connection = ldap_connection_mock

    return ldap_connection_mock


def practitioner_get(uid: Optional[str]) -> FhirPractitioner:
    handler = PractitionerHandler()
    handler_response = handler.get(APIGatewayProxyEvent(data={
        "resource": "/Practitioner",
        "queryStringParameters": {
            "identifier": uid
        }
    }))
    return handler_response.main_response[0]


def test_worker_handler():
    mock_ldap()
    response = practitioner_get("uid")
    assert_valid_ldaps_user(response)


def test_worker_handler_ldap_string_responses():
    # We've seen some inconsistency in the responses from ldap. Sometimes returning a list with a single value,
    # sometimes returning a string. We normally expect a single value array for most values, but this tests is for
    # strings instead. This makes sure that we don't error on an unexpected response format.
    ldap_connection_mock = MagicMock()
    nhs_person = NhsPerson({
        "uid": "uid",
        "sn": "Smith",
        "givenName": ["Bob"],
        "nhsMiddleNames": "John James",
        "personalTitle": ["Mr"],
        "nhsPersonStatus": "1",
    })
    ldap_connection_mock.return_value.search_active_nhs_person.return_value = [nhs_person, [], []]
    request_handlers.practitioner.get_connection = ldap_connection_mock

    response = practitioner_get("uid")

    assert response.id == "uid"
    assert response.resourceType == "Practitioner"
    assert response.active

    assert len(response.identifier) == 1
    assert response.identifier[0].system == "https://fhir.nhs.uk/Id/sds-user-id"
    assert response.identifier[0].value == "uid"

    assert len(response.name) == 1
    assert response.name[0].use == "usual"
    assert response.name[0].family == "Smith"
    assert response.name[0].given == ["Bob John James"]
    assert response.name[0].prefix == ["Mr"]


def test_missing_id():
    mock_ldap()

    with pytest.raises(HcwException) as e:
        practitioner_get(None)

    assert e.value.status_code == 400
    assert e.value.message == "Missing practitioner identifier"


def test_ldap_returns_error():
    ldap_connection_mock = mock_ldap()
    ldap_connection_mock.return_value.search_active_nhs_person.side_effect = HcwException(500, "LDAP Error", "exception")

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

        assert response.id == ""
        assert not any(filter(lambda x : x.system == "https://fhir.nhs.uk/Id/sds-user-id", response.identifier))

    def test_ldap_response_with_no_sn(self):
        mock_ldap(sn=None)

        response = practitioner_get("uid")

        assert response.name[0].family == ""

    def test_ldap_response_with_no_given_name(self):
        mock_ldap(given_name=None)

        response = practitioner_get("uid")

        # Just middle names
        assert response.name[0].given == ["John James"]

    def test_ldap_response_with_single_middle_name(self):
        mock_ldap(nhs_middle_names="Middle")

        response = practitioner_get("uid")

        assert response.name[0].given == ["Bob Middle"]

    def test_ldap_response_with_no_middle_name(self):
        mock_ldap(nhs_middle_names=None)

        response = practitioner_get("uid")

        assert response.name[0].given == ["Bob"]

    def test_ldap_response_with_empty_middle_names(self):
        mock_ldap(nhs_middle_names="")

        response = practitioner_get("uid")

        assert response.name[0].given == ["Bob"]

    def test_ldap_response_with_no_first_or_middle_name(self):
        mock_ldap(given_name=None, nhs_middle_names=None)

        response = practitioner_get("uid")

        assert response.name[0].given == [""]

    def test_ldap_response_with_no_title(self):
        mock_ldap(title=None)

        response = practitioner_get("uid")

        assert not hasattr(response.name[0], "prefix")
