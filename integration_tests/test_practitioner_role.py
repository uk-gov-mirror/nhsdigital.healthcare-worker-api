from typing import Optional

from example_practitioners import PractitionerExample, SINGLE_ROLE, \
    get_practitioners_example, NO_ROLE
from utils.integration_test_base import IntegrationTest
from utils.response_checks import check_practitioner_role_entry, check_practitioner_entry


class TestPractitionerRole(IntegrationTest):
    def send_practitioner_role_get(self, practitioner_id: Optional[int | str], method="GET",
                                    extra_query_params: Optional[dict] = None):
        query_params = {"practitioner.identifier": practitioner_id}
        if extra_query_params:
            query_params = query_params | extra_query_params
        return self.send_request(self.access_token, "PractitionerRole", query_params, method)

    @staticmethod
    def check_valid_response(response, practitioner: PractitionerExample):
        assert response.status_code == 200

        response_json = response.json()
        for i in range(0, len(practitioner.roles)):
            role = practitioner.roles[i]
            check_practitioner_role_entry(response_json[i], practitioner, role)

    @staticmethod
    def check_response_includes_practitioner(response, practitioner: PractitionerExample):
        response_json = response.json()
        found_entry = False
        for entry in response_json:
            if entry["resourceType"] == "Practitioner" and entry["id"] == practitioner.id:
                found_entry = True
                check_practitioner_entry(entry, practitioner)

        assert found_entry

    @staticmethod
    def check_response_includes_orgs(response, practitioner: PractitionerExample):
        response_json = response.json()

        for role in practitioner.roles:
            found_entry_for_role = False
            for entry in response_json:
                # TODO: Is this the right format for the organisation?
                if entry["resourceType"] == "Organisation" and entry["identifier"] == role.org_code:
                    found_entry_for_role = True
                    assert entry == {
                        "resourceType": "Organisation",
                        "identifier": role.org_code,
                        "name": role.org_name
                    }

            assert found_entry_for_role

    def test_get_practitioner_role_by_practitioner_id(self):
        response = self.send_practitioner_role_get(SINGLE_ROLE)

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_no_resource_type(response, "Practitioner")
        self.check_no_resource_type(response, "Organisation")

    def test_get_practitioner_role_no_roles(self):
        response = self.send_practitioner_role_get(NO_ROLE)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_practitioner_role_with_included_practitioner(self):
        response = self.send_practitioner_role_get(SINGLE_ROLE,
                                                    extra_query_params={"_include": "PractitionerRole:practitioner"})

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_practitioner(response, get_practitioners_example(SINGLE_ROLE))
        self.check_no_resource_type(response, "Organisation")

    def test_get_practitioner_role_with_included_organisation(self):
        response = self.send_practitioner_role_get(SINGLE_ROLE,
                                                    extra_query_params={"_include": "PractitionerRole:organization"})

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_no_resource_type(response, "Practitioner")
        self.check_response_includes_orgs(response, get_practitioners_example(SINGLE_ROLE))

    def test_get_practitioner_role_with_included_practitioner_and_organisation(self):
        includes = ["PractitionerRole:practitioner", "PractitionerRole:organization"]
        response = self.send_practitioner_role_get(SINGLE_ROLE, extra_query_params={"_include": includes})

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_practitioner(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_orgs(response, get_practitioners_example(SINGLE_ROLE))

    def test_get_practitioner_role_include_unknown_resource(self):
        includes = ["Unknown:practitioner", "PractitionerRole:practitioner", "PractitionerRole:organization"]
        response = self.send_practitioner_role_get(SINGLE_ROLE, extra_query_params={"_include": includes})

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_practitioner(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_orgs(response, get_practitioners_example(SINGLE_ROLE))

    def test_get_practitioner_role_include_unknown_field(self):
        includes = ["PractitionerRole:unknown", "PractitionerRole:practitioner", "PractitionerRole:organization"]
        response = self.send_practitioner_role_get(SINGLE_ROLE, extra_query_params={"_include": includes})

        self.check_valid_response(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_practitioner(response, get_practitioners_example(SINGLE_ROLE))
        self.check_response_includes_orgs(response, get_practitioners_example(SINGLE_ROLE))

    def test_get_practitioner_role_no_auth(self):
        response = self.send_request(None, "Practitioner", {"practitioner.identifier": SINGLE_ROLE})

        assert response.status_code == 401
        assert response.content == b""
