from statistics import correlation
from typing import Optional
from uuid import uuid4

import requests

from config.current_env import get_current_env


class IntegrationTest:
    @staticmethod
    def send_request(access_token: Optional[str], path: str, params: dict = None, method: str = "GET",
                        pass_correlation_id: bool = True):
        env = get_current_env()
        path = f"{env.base_url}/{path}"

        correlation_id = str(uuid4()) if pass_correlation_id else None
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": correlation_id
        }

        print(f"Sending request to {path} with correlation id {correlation_id}")
        return requests.request(
            method, path, params=params, headers=headers
        )
