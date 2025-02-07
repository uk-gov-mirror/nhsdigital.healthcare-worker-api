"""
Integration tests for the worker endpoint
"""
from typing import Optional

from example_practitioners import PractitionerExample, KNOWN_USER, NO_PREFIX_OR_MIDDLE_NAME, get_practitioners_example, \
    MULTIPLE_MIDDLE_NAMES, SINGLE_ROLE
from utils.integration_test_base import IntegrationTest
from utils.response_checks import check_practitioner_entry, check_practitioner_role_entry, check_bundle, check_entry_wrapper


class TestWorker(IntegrationTest):
    def send_worker_get(self, worker_id: Optional[int | str], method="GET", extra_query_params: Optional[dict] = None):
        query_params = {"identifier": worker_id}
        if extra_query_params:
            query_params = query_params | extra_query_params
        return self.send_request(self.access_token, "Practitioner", query_params, method=method)

    @staticmethod
    def check_valid_response(response, practitioner: PractitionerExample):
        assert response.status_code == 200

        response_json = response.json()
        check_bundle(response_json, 1)
        main_entry = [x for x in response_json["entry"] if x["search"]["mode"] == "match"][0]
        check_practitioner_entry(main_entry["resource"], practitioner)

    @staticmethod
    def check_response_includes_practitioner_roles(response, practitioner: PractitionerExample):
        response_json = response.json()

        for role in practitioner.roles:
            found_entry = False
            for entry in response_json["entry"]:
                entry_resource = entry["resource"]
                if entry_resource["resourceType"] == "PractitionerRole" and entry_resource["id"] == role.role_profile_id:
                    found_entry = True
                    check_practitioner_role_entry(entry_resource, practitioner, role)

            assert found_entry

    def test_get_practitioner(self):
        response = self.send_worker_get(KNOWN_USER)
        self.check_valid_response(response, get_practitioners_example(KNOWN_USER))

    def test_get_practitioner_without_middle_name_or_prefix(self):
        response = self.send_worker_get(NO_PREFIX_OR_MIDDLE_NAME)
        self.check_valid_response(response, get_practitioners_example(NO_PREFIX_OR_MIDDLE_NAME))

    def test_get_practitioner_with_multiple_middles_names(self):
        response = self.send_worker_get(MULTIPLE_MIDDLE_NAMES)
        self.check_valid_response(response, get_practitioners_example(MULTIPLE_MIDDLE_NAMES))

    def test_get_missing_worker(self):
        response = self.send_worker_get(999)

        assert response.status_code == 404
        assert response.json() == {
            "resourceType": "OperationOutcome",
            "issue": [{
                "code": "not-found",
                "severity": "error",
                "details": {
                    "coding": [{
                        "code": "MSG_NO_MATCH",
                        "display": "No Resource found matching the query 999",
                        "system": "http://hl7.org/fhir/operation-outcome"}]
                }
            }]
        }

    def test_wrong_url(self):
        response = self.send_request(self.access_token, "invalid_url")

        assert response.status_code == 404
        assert response.content == b""

    def test_wrong_method(self):
        response = self.send_request(self.access_token, "Practitioner", {"identifier": 999}, method="POST")

        assert response.status_code == 404
        assert response.content == b""

    def test_get_special_characters_worker_id(self):
        response = self.send_worker_get("invalid_id!@£⚠️")

        assert response.status_code == 404
        assert response.json() == {
            "resourceType": "OperationOutcome",
            "issue": [{
                "code": "not-found",
                "severity": "error",
                "details": {
                    "coding": [{
                        "code": "MSG_NO_MATCH",
                        "display": "No Resource found matching the query invalid_id!@£⚠️",
                        "system": "http://hl7.org/fhir/operation-outcome"}]
                }
            }]
        }

    def test_without_auth(self):
        response = self.send_request(None, "Practitioner", {"identifier": KNOWN_USER})

        assert response.status_code == 401
        assert response.content == b""

    def test_invalid_auth(self):
        response = self.send_request("invalid", "Practitioner", {"identifier": KNOWN_USER})

        assert response.status_code == 401
        assert response.content == b""

    def test_missing_correlation_id(self):
        response = self.send_request(self.access_token, "Practitioner", {"identifier": KNOWN_USER},
                                        pass_correlation_id=False)
        self.check_valid_response(response, get_practitioners_example(KNOWN_USER))

    def test_practitioner_with_revinclude_role(self):
        includes = {"_revinclude": "PractitionerRole:practitioner"}
        response = self.send_worker_get(SINGLE_ROLE, extra_query_params=includes)

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_practitioner_roles(response, get_practitioners_example(SINGLE_ROLE))

    def test_practitioner_with_revinclude_unknown_resource(self):
        includes = {"_revinclude": ["Unknown:practitioner", "PractitionerRole:practitioner"]}
        response = self.send_worker_get(SINGLE_ROLE, extra_query_params=includes)

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_practitioner_roles(response, get_practitioners_example(SINGLE_ROLE))

    def test_practitioner_with_revinclude_unknown_field(self):
        includes = {"_revinclude": ["PractitionerRole:unknown", "PractitionerRole:practitioner"]}
        response = self.send_worker_get(SINGLE_ROLE, extra_query_params=includes)

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_practitioner_roles(response, get_practitioners_example(SINGLE_ROLE))

