import os.path
import sys
import uuid
from time import time
import jwt
import requests

from config.base_environment import EnvironmentConfig
from config.pr_environment import PrEnvironmentConfig


def generate_from_command_line():
    if len(sys.argv) != 2:
        print("Expected format poetry run start <api_key>")
        exit(1)

    client_id = sys.argv[1]
    access_token = generate_access_token(PrEnvironmentConfig(client_id, ""))
    print(f"Access token: {access_token}")


def generate_access_token(env: EnvironmentConfig, silent=False):
    if not silent:
        # This can be a useful confirmation for integration tests, but is messy during an NFT run
        print(f"client id = {env.client_id}")

    private_key_filename = f"{os.path.dirname(os.path.realpath(__file__))}/test-1.pem"
    key_id = "test-1"

    claims = {
        "sub": env.client_id,
        "iss": env.client_id,
        "jti": str(uuid.uuid4()),
        "aud": env.realm_url,
        "exp": int(time()) + 300,
    }

    with open(private_key_filename, "rb") as f:
        private_key = f.read()

    client_assertion = jwt.encode(
        claims, private_key, algorithm="RS512", headers={'kid': key_id}
    )

    token_response = requests.post(
        env.realm_url,
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": client_assertion,
        },
    )

    response = token_response.json()
    if "access_token" not in response:
        raise Exception(f"Failed to fetch access token, received error from token request: {response}")

    access_token = response["access_token"]
    expires_at = int(response["expires_in"]) + int(response["issued_at"])
    return access_token, expires_at
