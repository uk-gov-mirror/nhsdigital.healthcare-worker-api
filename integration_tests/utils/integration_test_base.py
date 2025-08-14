from statistics import correlation
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

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

        # Add timestamp to request logging
        local_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
        print(f"[{local_time}] Sending {method} request to {path}")
        print(f"[{local_time}] Correlation ID: {correlation_id}")

        request_start = datetime.now()
        response = requests.request(method, path, params=params, headers=headers)
        request_duration = (datetime.now() - request_start).total_seconds()

        response_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
        print(f"[{response_time}] Response received: {response.status_code} (took {request_duration:.3f}s)")

        # Log errors with timestamp for easy CloudWatch correlation
        if response.status_code >= 400:
            print(f"[{response_time}] ERROR RESPONSE: Status {response.status_code}")
            print(f"[{response_time}] Response body: {response.text}")

        return response

    @pytest.fixture(autouse=True, scope="session")
    def log_test_session(self):
        session_start = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
        print(f"\n{'='*60}")
        print(f"INTEGRATION TEST SESSION STARTED: {session_start}")
        print(f"{'='*60}")
        yield
        session_end = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
        print(f"\n{'='*60}")
        print(f"INTEGRATION TEST SESSION ENDED: {session_end}")
        print(f"{'='*60}")

    @pytest.fixture(autouse=True)
    def resource(self):
        env = get_current_env()
        if not isinstance(env, SandboxEnvironmentConfig):
            self.access_token, _ = generate_access_token(env.client_id, env.realm_url)
        else:
            self.access_token = "no_auth_required"

        yield

    @staticmethod
    def check_no_resource_type(response, resource_type: str):
        response_json = response.json()

        for entry in response_json["entry"]:
            if entry["resource"]["resourceType"] == resource_type:
                fail(f"Expected no {resource_type} entries in response")

    @staticmethod
    def assert_with_timestamp(condition, message=""):
        if not condition:
            error_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
            timestamped_message = f"[{error_time}] ASSERTION FAILED: {message}"
            print(timestamped_message)
            fail(timestamped_message)

    @staticmethod
    def assert_status_code_with_timestamp(response, expected_status, correlation_id=None):
        if response.status_code != expected_status:
            error_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
            correlation_info = f" (Correlation ID: {correlation_id})" if correlation_id else ""
            error_msg = f"[{error_time}] Expected status {expected_status}, got {response.status_code}{correlation_info}"
            print(error_msg)
            print(f"[{error_time}] Response body: {response.text}")
            fail(error_msg)
