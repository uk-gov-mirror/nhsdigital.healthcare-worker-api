"""
Integration tests for the worker endpoint
"""
from typing import Optional

import pytest

from config.current_env import get_current_env
from utils.generate_access_token import generate_access_token
from utils.integration_test_base import IntegrationTest


class TestWorker(IntegrationTest):
    access_token: Optional[str]

    def send_worker_get(self, worker_id: Optional[int]):
        return self.send_request(self.access_token, "Practitioner", {"identifier": worker_id})

    @pytest.fixture(autouse=True)
    def resource(self):
        env = get_current_env()
        self.access_token = generate_access_token(env.client_id)

        yield

    def test_get_worker(self):
        response = self.send_worker_get(150549950108)

        assert response.status_code == 200

        worker_details = response.json()
        assert worker_details == {
            "id": "150549950108",
            "resourceType": "Practitioner",
            "active": True,
            "identifier": [{"system": "https://fhir.nhs.uk/Id/sds-user-id", "value": "150549950108"}],
            "name": [{"family": "Banshpal", "given": "Jitendra", "prefix": "Mr", "use": "usual"}]
        }

    def test_get_missing_worker(self):
        response = self.send_worker_get(999)
        worker_details = response.json()

        assert response.status_code == 404
        assert worker_details == {"error": "User with id 999 not found"}
