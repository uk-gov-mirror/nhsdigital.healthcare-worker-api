import json
import os
import uuid
from datetime import datetime
from enum import IntEnum
from ssl import CERT_REQUIRED
from typing import Optional

import boto3
from botocore.config import Config
from ldap3 import Tls, Server, Connection, SAFE_SYNC
from ldap3.core.exceptions import LDAPException

from hcw_exception import HcwException
from ldap.connection import HcwLdapConnection
from ldap.nhs_person import NhsPerson, NhsOrgPersonRole, NhsOrgPerson
from logs.log import Log

logger = Log("ldap_connection")


class LdapErrorCode(IntEnum):
    NOT_FOUND = 32


class RealHcwLdapConnection(HcwLdapConnection):
    connection: Connection
    bind_time: datetime

    def __init__(self):
        self.client = boto3.client("secretsmanager", config=Config(region_name="eu-west-2"))
        self.connection = self.connect()
        logger.info("LDAP connection established")

    def get_secret(self, secret_id) -> dict:
        return json.loads(self.client.get_secret_value(SecretId=secret_id)["SecretString"])

    @staticmethod
    def save_secret_to_file(secret: str) -> str:
        filename = f"/tmp/{uuid.uuid4()}.pem"  # NOSONAR python:S5443
        with open(filename, "w") as f:
            f.write(secret)

        return filename

    def connect(self) -> Optional[Connection]:
        logger.info("About to fetch secrets")
        if "LDAP_CREDENTIALS_SECRET_ID" not in os.environ:
            logger.error("Could not form LDAP connection")
            return None

        ldap_credentials = self.get_secret(os.environ["LDAP_CREDENTIALS_SECRET_ID"])
        logger.info("Fetched secrets")

        server_cert_filename = self.save_secret_to_file(ldap_credentials["LDAP_SERVER_CERT"])
        mtls_client_private_key_filename = self.save_secret_to_file(ldap_credentials["MTLS_CLIENT_KEY"])
        mtls_client_cert_filename = self.save_secret_to_file(ldap_credentials["MTLS_CLIENT_CERT"])
        logger.info("Saved secrets to tmp file")

        username = ldap_credentials["LDAP_USERNAME"]
        password = ldap_credentials["PASSWORD"]

        try:
            tls = Tls(
                local_private_key_file=mtls_client_private_key_filename,
                local_certificate_file=mtls_client_cert_filename,
                ca_certs_file=server_cert_filename,
                validate=CERT_REQUIRED
            )
            server = Server(os.environ["LDAP_GATEWAY_URL"], use_ssl=True, tls=tls)

            connection = Connection(server, user=username, password=password, client_strategy=SAFE_SYNC)

            bound = connection.bind()
            if not bound:
                raise HcwException(500, "Could not bind to LDAP server")

            self.bind_time = datetime.now()

            return connection
        except LDAPException as e:
            raise HcwException(500, f"Error connecting to LDAP: {e}", "Error connecting to LDAP")

    @staticmethod
    def check_response(uid, success, result):
        result_code = result["result"]
        if result_code == LdapErrorCode.NOT_FOUND:
            raise HcwException(404, f"User with id {uid} not found")

        if not success:
            raise HcwException(500, f"Unknown error from LDAP request. Result: {result}",
                                "Unknown error from LDAP request")

    @staticmethod
    def find_by_type(response, object_class):
        return map(lambda r: r["attributes"], filter(lambda r: object_class in r["attributes"]["objectClass"], response))

    @staticmethod
    def get_nhs_person(response) -> dict[str, str]:
        return next(RealHcwLdapConnection.find_by_type(response, "nhsPerson"))

    @staticmethod
    def get_org_person(response) -> list[dict[str, str]]:
        return list(RealHcwLdapConnection.find_by_type(response, "nhsOrgPerson"))

    @staticmethod
    def get_org_roles(response) -> list[dict[str, str]]:
        return list(RealHcwLdapConnection.find_by_type(response, "nhsOrgPersonRole"))

    def search_active_nhs_person(self, uid: str, allow_retry: bool = True) -> [NhsPerson, list[NhsOrgPerson], list[NhsOrgPersonRole]]:
        try:
            logger.info("Searching LDAP for nhsPerson")

            return_attributes = ["uid", "Sn", "givenName", "nhsMiddleNames", "personalTitle", "nhsPersonStatus",
                                    "objectclass", "uniqueIdentifier", "nhsOpenDate", "nhsIDCode", "o",
                                    "nhsBusinessFunctionsCodes", "nhsJobRole", "nhsJobRoleCode", "nhsBusinessFunctions",
                                    "nhsCloseDate"]
            success, result, response, request = self.connection.search(f"uid={uid},ou=people,o=nhs",
                                                                        "(objectclass=*)",
                                                                        attributes=return_attributes)

            logger.info(f"Received LDAP response, success: {success}")

            self.check_response(uid, success, result)

            practitioner = NhsPerson(self.get_nhs_person(response))
            org_persons = [NhsOrgPerson(r) for r in self.get_org_person(response)]
            roles = [NhsOrgPersonRole(r) for r in self.get_org_roles(response)]

            active_roles = []
            for role in roles:
                if not role.role_stopped or role.role_stopped > datetime.now().date():
                    role.org_person = next(filter(lambda op: op.nhs_id_code == role.nhs_id_code, org_persons))
                    role.practitioner = practitioner
                    active_roles.append(role)

            return practitioner, org_persons, active_roles

        except LDAPException as e:
            if allow_retry:
                logger.warning(f"Got an LDAP connection error {e}. Attempting to reconnect.")
                self.connection = self.connect()
                logger.info("LDAP connection re-established")
                return self.search_active_nhs_person(uid, allow_retry=False)
            else:
                raise HcwException(500, "LDAP connection error and retry failed", "Error connecting to LDAP")
