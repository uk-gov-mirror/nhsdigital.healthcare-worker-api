from typing import Optional

from example_practitioners import PractitionerExample, SINGLE_ROLE, \
    get_practitioners_example, NO_ROLE, MISSING_ROLE_OPEN_DATE_PAST_CLOSE, MISSING_ROLE_DATES
from utils.integration_test_base import IntegrationTest
from utils.response_checks import check_practitioner_role_entry, check_practitioner_entry, check_bundle, check_entry_wrapper


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
        check_bundle(response_json, 1)
        for i in range(0, len(practitioner.roles)):
            role = practitioner.roles[i]
            entry = [x["resource"] for x in response_json["entry"] if x["search"]["mode"] == "match" and
                        x["resource"]["identifier"][0]["value"] == role.role_profile_id][0]
            check_practitioner_role_entry(entry, practitioner, role)

    @staticmethod
    def check_response_includes_practitioner(response, practitioner: PractitionerExample):
        response_json = response.json()
        found_entry = False
        for entry in response_json["entry"]:
            entry_resource = entry["resource"]
            if entry_resource["resourceType"] == "Practitioner" and entry_resource["id"] == practitioner.id:
                found_entry = True
                check_entry_wrapper(entry, "include")
                check_practitioner_entry(entry_resource, practitioner)

        assert found_entry

    @staticmethod
    def check_response_includes_orgs(response, practitioner: PractitionerExample):
        response_json = response.json()

        for role in practitioner.roles:
            found_entry_for_role = False
            for entry in response_json["entry"]:
                entry_resource = entry["resource"]
                if entry_resource["resourceType"] == "Organization" and entry_resource["identifier"][0]["value"] == role.org_code:
                    found_entry_for_role = True
                    assert entry_resource == {
                        "resourceType": "Organization",
                        "id": role.org_code,
                        "identifier": [{
                            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                            "value": role.org_code,
                        }],
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
        assert response.json() == {"entry": [], "resourceType": "Bundle", "total": 0, "type": "searchset",
                                    "link": [{"relation": "self", "url": "https://https://internal-dev.api.service.nhs.uk/healthcare-worker/PractitionerRole"}]}

    def test_get_practitioner_role_missing_open_date_past_close_filtered_out(self):
        """Test that roles with missing open date + past close date are filtered out"""
        response = self.send_practitioner_role_get(MISSING_ROLE_OPEN_DATE_PAST_CLOSE)

        # Should return 200 (no crash when processing missing open date)
        assert response.status_code == 200

        response_json = response.json()

        # Get the specific role that should be filtered out from the test data
        expected_practitioner = get_practitioners_example(MISSING_ROLE_OPEN_DATE_PAST_CLOSE)
        filtered_role_id = expected_practitioner.roles[0].role_profile_id  # Role with missing open date + past close date

        # Verify the problematic role is NOT in the response
        returned_role_ids = [entry["resource"]["id"] for entry in response_json.get("entry", [])
            if entry["resource"]["resourceType"] == "PractitionerRole"]

        assert filtered_role_id not in returned_role_ids, f"Role {filtered_role_id} should be filtered out but was found in response"

        # The practitioner might have other active roles, so we don't enforce empty response
        # We just ensure the problematic role is excluded

    def test_get_practitioner_role_missing_both_dates_included(self):
        """Test that roles with missing both open and close dates are included"""
        response = self.send_practitioner_role_get(MISSING_ROLE_DATES)

        # Should return 200 (no crash when processing missing dates)
        assert response.status_code == 200

        response_json = response.json()

        # Get the specific role that should be included from the test data
        expected_practitioner = get_practitioners_example(MISSING_ROLE_DATES)
        included_role_id = expected_practitioner.roles[0].role_profile_id  # Role with missing both dates

        # Verify the role with missing dates IS in the response
        returned_role_ids = [entry["resource"]["id"] for entry in response_json.get("entry", [])
            if entry["resource"]["resourceType"] == "PractitionerRole"]

        assert included_role_id in returned_role_ids, f"Role {included_role_id} should be included but was not found in response"

        # The practitioner might have other roles too, we just ensure this specific one is included

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
