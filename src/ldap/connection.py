import os
import uuid
from enum import IntEnum
from ssl import CERT_REQUIRED

import boto3
import botocore
from botocore.config import Config
from ldap3 import Tls, Server, Connection, SAFE_SYNC, AUTO_BIND_TLS_BEFORE_BIND

from hcw_exception import HcwException
from ldap.nhs_person import NhsPerson
from logs.log import Log

logger = Log("ldap_connection")


class LdapErrorCode(IntEnum):
    NOT_FOUND = 32


class HcwLdapConnection:
    connection: Connection

    def __init__(self):
        self.client = boto3.client("secretsmanager", config=Config(region_name="eu-west-2"))
        self.connection = self.connect()

    def get_secret(self, secret_id) -> str:
        return self.client.get_secret_value(SecretId=secret_id)["SecretString"]

    def save_secret_to_file(self, secret_id) -> str:
        secret = self.get_secret(secret_id)

        filename = f"/tmp/{uuid.uuid4()}.pem"  # NOSONAR python:S5443
        with open(filename, "w") as f:
            f.write(secret)

        return filename

    def connect(self) -> Connection:
        server_cert_filename = self.save_secret_to_file(os.environ["LDAP_SERVER_CERT_ID"])
        mtls_client_private_key_filename = self.save_secret_to_file(os.environ["MTLS_CLIENT_KEY_ID"])
        mtls_client_cert_filename = self.save_secret_to_file(os.environ["MTLS_CLIENT_CERT_ID"])

        tls = Tls(
            local_private_key_file=mtls_client_private_key_filename,
            local_certificate_file=mtls_client_cert_filename,
            ca_certs_file=server_cert_filename,
            validate=CERT_REQUIRED
        )
        server = Server(os.environ["LDAP_GW_URL"], use_ssl=True, tls=tls)

        username = os.environ["LDAP_USERNAME"]
        password = self.get_secret(os.environ["LDAP_PASSWORD_ID"])
        return Connection(server, user=username, password=password, client_strategy=SAFE_SYNC, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)

    def search_active_nhs_person(self, uid: str) -> NhsPerson:
        logger.info("Searching LDAP for nhsPerson")
        if not self.connection:
            raise HcwException(500, "Attempted to search before establishing an LDAP connection")

        return_attributes = ["uid", "Sn", "givenName", "nhsMiddleNames", "personalTitle", "nhsPersonStatus"]
        success, result, response, _ = self.connection.search(f"uid={uid},ou=people,o=nhs", "(objectclass=nhsPerson)",
                                                                attributes=return_attributes)
        logger.info(f"Received LDAP response, success: {success}")

        result_code = result["result"]
        if result_code == LdapErrorCode.NOT_FOUND:
            raise HcwException(404, f"User with id {uid} not found")

        if not success:
            raise HcwException(500, f"Unknown error from LDAP request. Result: {result}",
                                "Unknown error from LDAP request")

        if len(response) > 1:
            raise HcwException(500, f"Found multiple users with id {uid}")

        attrs = response[0]["attributes"]

        logger.info(f"Found attrs of {attrs}")
        if attrs["nhsPersonStatus"] != "1":
            # Don't return active users. Deliberately returning a "not found" response so we don't leak any information
            raise HcwException(404, f"User with id {uid} not found")

        return NhsPerson(
            attrs["uid"],
            attrs["sn"],
            attrs["givenName"],
            attrs["nhsMiddleNames"],
            attrs["personalTitle"],
            attrs["nhsPersonStatus"]
        )
