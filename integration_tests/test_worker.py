"""
Integration tests for the worker endpoint
"""
from typing import Optional

import pytest

from config.current_env import get_current_env
from utils.generate_access_token import generate_access_token
from utils.integration_test_base import IntegrationTest

KNOWN_USER_ID = 150549950108


class TestWorker(IntegrationTest):
    access_token: Optional[str]

    def send_worker_get(self, worker_id: Optional[int | str], method="GET"):
        return self.send_request(self.access_token, "Practitioner", {"identifier": worker_id}, method=method)

    @staticmethod
    def check_valid_response(response):
        assert response.status_code == 200
        assert response.json() == {
            "id": "150549950108",
            "resourceType": "Practitioner",
            "active": True,
            "identifier": [{"system": "https://fhir.nhs.uk/Id/sds-user-id", "value": "150549950108"}],
            "name": [{"family": "Banshpal", "given": "Jitendra", "prefix": "Mr", "use": "usual"}]
        }

    @pytest.fixture(autouse=True)
    def resource(self):
        env = get_current_env()
        self.access_token = generate_access_token(env.client_id)

        yield

    def test_get_worker(self):
        response = self.send_worker_get(KNOWN_USER_ID)
        self.check_valid_response(response)

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
        response = self.send_request(None, "Practitioner", {"identifier": KNOWN_USER_ID})

        assert response.status_code == 401
        assert response.content == b""

    def test_invalid_auth(self):
        response = self.send_request("invalid", "Practitioner", {"identifier": KNOWN_USER_ID})

        assert response.status_code == 401
        assert response.content == b""

    def test_missing_correlation_id(self):
        response = self.send_request(self.access_token, "Practitioner", {"identifier": KNOWN_USER_ID},
                                        pass_correlation_id=False)
        self.check_valid_response(response)
