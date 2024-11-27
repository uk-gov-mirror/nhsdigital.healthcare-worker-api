import os
from datetime import datetime
from uuid import uuid4

from locust import HttpUser, task, between
from locust.log import setup_logging

from utils.generate_access_token import generate_access_token

setup_logging("INFO")


class HcwTest(HttpUser):
    access_token: str = None
    token_expires_at: int = None
    wait_time = between(5, 10)

    def on_start(self):
        self.access_token, self.token_expires_at = generate_access_token(os.environ["CLIENT_ID"], silent=True)

    @task
    def practitioner_get(self):
        if datetime.now().timestamp() < self.token_expires_at:
            self.on_start()

        self.client.get("/Practitioner?identifier=150549950108",
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "X-Correlation-ID": str(uuid4())
                        })
