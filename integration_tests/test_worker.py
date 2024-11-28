"""
Integration tests for the worker endpoint
"""
from typing import Optional

import pytest

from config.current_env import get_current_env
from config.sandbox import SandboxEnvironmentConfig
from example_practitioners import PractitionerExample, KNOWN_USER, NO_PREFIX_OR_MIDDLE_NAME, get_practitioners_example, \
    MULTIPLE_MIDDLE_NAMES
from utils.generate_access_token import generate_access_token
from utils.integration_test_base import IntegrationTest


class TestWorker(IntegrationTest):
    access_token: Optional[str]

    def send_worker_get(self, worker_id: Optional[int | str], method="GET"):
        return self.send_request(self.access_token, "Practitioner", {"identifier": worker_id}, method=method)

    @staticmethod
    def check_valid_response(response, practitioner: PractitionerExample):
        assert response.status_code == 200
        assert response.json() == {
            "id": practitioner.id,
            "resourceType": "Practitioner",
            "active": True,
            "identifier": [{"system": "https://fhir.nhs.uk/Id/sds-user-id", "value": practitioner.id}],
            "name": [{"family": practitioner.family, "given": practitioner.given, "prefix": practitioner.prefix,
                        "use": "usual"}]
        }

    @pytest.fixture(autouse=True)
    def resource(self):
        env = get_current_env()
        if not isinstance(env, SandboxEnvironmentConfig):
            self.access_token, _ = generate_access_token(env)
        else:
            self.access_token = "no_auth_required"

        yield

    def test_get_worker(self):
        response = self.send_worker_get(KNOWN_USER)
        self.check_valid_response(response, get_practitioners_example(KNOWN_USER))

    def test_get_worker_without_middle_name_or_prefix(self):
        response = self.send_worker_get(NO_PREFIX_OR_MIDDLE_NAME)
        self.check_valid_response(response, get_practitioners_example(NO_PREFIX_OR_MIDDLE_NAME))

    def test_get_worker_with_multiple_middles_names(self):
        response = self.send_worker_get(MULTIPLE_MIDDLE_NAMES)
        self.check_valid_response(response, get_practitioners_example(MULTIPLE_MIDDLE_NAMES))

    def test_get_missing_worker(self):
        response = self.send_worker_get(999)

        assert response.status_code == 404
        assert response.json() == {"error": "User with id 999 not found"}

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
        assert response.json() == {"error": "User with id invalid_id!@£⚠️ not found"}

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
