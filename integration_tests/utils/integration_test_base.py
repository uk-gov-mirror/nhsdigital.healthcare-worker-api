from statistics import correlation
from typing import Optional
from uuid import uuid4

import pytest
import requests
from _pytest.outcomes import fail

from config.current_env import get_current_env
from config.sandbox import SandboxEnvironmentConfig
from utils.generate_access_token import generate_access_token


class IntegrationTest:
    access_token: Optional[str]

    @staticmethod
    def send_request(access_token: Optional[str], path: str, params: dict = None, method: str = "GET",
                        pass_correlation_id: bool = True, query_params: str = ""):
        env = get_current_env()
        path = f"{env.base_url}/{path}?{query_params}"

        correlation_id = str(uuid4()) if pass_correlation_id else None
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": correlation_id
        }

        print(f"Sending request to {path} with correlation id {correlation_id}")
        return requests.request(
            method, path, params=params, headers=headers
        )

    @pytest.fixture(autouse=True)
    def resource(self):
        env = get_current_env()
        if not isinstance(env, SandboxEnvironmentConfig):
            self.access_token, _ = generate_access_token(env)
        else:
            self.access_token = "no_auth_required"

        yield

    @staticmethod
    def check_no_resource_type(response, resource_type: str):
        response_json = response.json()

        for entry in response_json["entry"]:
            if entry["resource"]["resourceType"] == resource_type:
                fail(f"Expected no {resource_type} entries in response")
