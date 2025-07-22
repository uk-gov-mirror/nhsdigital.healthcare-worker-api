import json
import os
import time
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
        init_start_time = time.time()
        logger.info("Starting LDAP connection initialization", "LDAP_INIT_START", "null")

        # Time the boto3 client creation
        client_start = time.time()
        self.client = boto3.client("secretsmanager", config=Config(region_name="eu-west-2"))
        client_duration = time.time() - client_start
        logger.info(f"boto3 client creation took {client_duration:.2f}s", "BOTO3_CLIENT_TIMING", "null")

        # Time the connection establishment
        connect_start = time.time()
        self.connection = self.connect()
        connect_duration = time.time() - connect_start
        logger.info(f"LDAP connection setup took {connect_duration:.2f}s", "LDAP_CONNECT_TIMING", "null")

        # Log total initialization time
        total_duration = time.time() - init_start_time
        logger.info(f"Total LDAP initialization took {total_duration:.2f}s", "LDAP_INIT_TOTAL", "null")

    def connect(self) -> Optional[Connection]:
        start_time = time.time()
        logger.info("About to fetch secrets", "SECRETS_CONN_START", "null")

        # Time the environment check
        env_check_start = time.time()
        if "LDAP_CREDENTIALS_SECRET_ID" not in os.environ:
            logger.error("Could not form LDAP connection", "LDAP_CONN_ERROR", "null")
            return None
        env_check_duration = time.time() - env_check_start
        logger.info(f"Environment check took {env_check_duration:.3f}s", "ENV_CHECK_TIMING", "null")

        # Time the secret fetching
        secret_start = time.time()
        secret_string = self.client.get_secret_value(SecretId=os.environ["LDAP_CREDENTIALS_SECRET_ID"])["SecretString"]
        secret_duration = time.time() - secret_start
        logger.info(f"Secret fetch took {secret_duration:.2f}s", "SECRET_CALL_TIMING", "null")

        # Time JSON parsing
        json_start = time.time()
        secret = json.loads(secret_string)
        json_duration = time.time() - json_start
        logger.info(f"JSON parsing took {json_duration:.3f}s", "JSON_PARSE_TIMING", "null")

        # Log secret size (without content)
        secret_size = len(secret_string)
        logger.info(f"Secret size: {secret_size} bytes", "SECRET_SIZE_INFO", "null")

        # Time file operations
        ca_cert_start = time.time()
        with open("/tmp/ca_cert.pem", "w") as f:
            f.write(secret["ca_cert"])
        ca_cert_duration = time.time() - ca_cert_start
        logger.info(f"CA cert file write took {ca_cert_duration:.3f}s", "CA_CERT_FILE_TIMING", "null")

        client_cert_start = time.time()
        with open("/tmp/client_cert.pem", "w") as f:
            f.write(secret["client_cert"])
        client_cert_duration = time.time() - client_cert_start
        logger.info(f"Client cert file write took {client_cert_duration:.3f}s", "CLIENT_CERT_FILE_TIMING", "null")

        client_key_start = time.time()
        with open("/tmp/client_key.pem", "w") as f:
            f.write(secret["client_key"])
        client_key_duration = time.time() - client_key_start
        logger.info(f"Client key file write took {client_key_duration:.3f}s", "CLIENT_KEY_FILE_TIMING", "null")

        # Time TLS setup
        tls_start = time.time()
        tls = Tls(
            local_private_key_file="/tmp/client_key.pem",
            local_certificate_file="/tmp/client_cert.pem",
            validate=CERT_REQUIRED,
            version=None,
            ca_certs_file="/tmp/ca_cert.pem",
        )
        server = Server(secret["ldap_host"], port=secret["ldap_port"], use_ssl=True, tls=tls)
        tls_duration = time.time() - tls_start
        logger.info(f"TLS setup took {tls_duration:.3f}s", "TLS_SETUP_TIMING", "null")

        # Time the LDAP bind
        bind_start = time.time()
        try:
            connection = Connection(server, user=secret["ldap_user"], password=secret["ldap_password"],
                                  auto_bind=True, client_strategy=SAFE_SYNC)
            self.bind_time = datetime.now()
            bind_duration = time.time() - bind_start
            logger.info(f"LDAP bind took {bind_duration:.3f}s", "LDAP_BIND_TIMING", "null")

            total_duration = time.time() - start_time
            logger.info(f"Total connect() took {total_duration:.2f}s", "CONNECT_TOTAL_TIMING", "null")
            logger.info("Fetched secrets", "SECRETS_CONN_SUCCESS", "null")
            return connection
        except LDAPException as e:
            bind_duration = time.time() - bind_start
            total_duration = time.time() - start_time
            logger.error(f"LDAP bind failed after {bind_duration:.3f}s, total {total_duration:.2f}s: {e}",
                        "LDAP_BIND_ERROR", "null")
            logger.error("Could not bind to LDAP", "LDAP_CONN_ERROR", "null")
            return None

    @staticmethod
    def check_response(uid, success, result):
        result_code = result["result"]
        if result_code == LdapErrorCode.NOT_FOUND:
            raise HcwException(404, f"User with id {uid} not found", "unknown")

        if not success:
            raise HcwException(500, f"Unknown error from LDAP request. Result: {result}", "exception",
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
            logger.info("Searching LDAP for nhsPerson","SEARCH_PERSON_START", uid)

            # Removed "nhsPrinOcc", "nhsRPSGB"  "nhsSiteNames", "nhsSiteCodes"
            return_attributes = ["uid", "Sn", "givenName", "nhsMiddleNames", "personalTitle", "nhsPersonStatus",
                                    "objectclass", "uniqueIdentifier", "nhsOrgOpenDate", "nhsIDCode", "o",
                                    "nhsBusinessFunctionsCodes", "nhsJobRole", "nhsJobRoleCode", "nhsBusinessFunctions",
                                    "nhsOrgCloseDate", "nhsGMC", "nhsGDP", "nhsGDC", "nhsRCN",
                                    "nhsNMC", "nhsConsultant", "nhsGMP", "nhsOcsPrCode"]
            success, result, response, request = self.connection.search(f"uid={uid},ou=people,o=nhs",
                                                                        "(objectclass=*)",
                                                                        attributes=return_attributes)
            logger.info(f"Received LDAP response, success: {success}","SEARCH_PERSON_SUCCESS", uid)

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
                logger.warning(f"Got an LDAP connection error {e}. Attempting to reconnect.","LDAP_RECON_START", "null")
                self.connection = self.connect()
                logger.info("LDAP connection re-established", "LDAP_RECON_SUCCESS", "null")
                return self.search_active_nhs_person(uid, allow_retry=False)
            else:
                raise HcwException(500, f"LDAP connection error and retry failed {e}", "exception","Error connecting to LDAP")
