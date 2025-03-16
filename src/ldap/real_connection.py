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
        logger.info("Initializing RealHcwLdapConnection")
        self.client = boto3.client("secretsmanager", config=Config(region_name="eu-west-2"))
        self.connection = self.connect()
        logger.info("LDAP connection established")

    def get_secret(self, secret_id) -> dict:
        logger.info(f"Getting secret from SecretManager: {secret_id}")
        try:
            secret_value = self.client.get_secret_value(SecretId=secret_id)
            logger.info("Secret retrieved successfully")
            return json.loads(secret_value["SecretString"])
        except Exception as e:
            logger.error(f"Error retrieving secret: {e}")
            raise

    @staticmethod
    def save_secret_to_file(secret: str) -> str:
        filename = f"/tmp/{uuid.uuid4()}.pem"  # NOSONAR python:S5443
        with open(filename, "w") as f:
            f.write(secret)

        return filename

    def connect(self) -> Optional[Connection]:
        logger.info("About to fetch secrets")
        if "LDAP_CREDENTIALS_SECRET_ID" not in os.environ:
            logger.error("Could not form LDAP connection - LDAP_CREDENTIALS_SECRET_ID not in environment variables")
            return None

        secret_id = os.environ["LDAP_CREDENTIALS_SECRET_ID"]
        logger.info(f"Using secret ID: {secret_id}")
        try:
            ldap_credentials = self.get_secret(secret_id)
            logger.info("Fetched secrets")

            server_cert_filename = self.save_secret_to_file(ldap_credentials["LDAP_SERVER_CERT"])
            mtls_client_private_key_filename = self.save_secret_to_file(ldap_credentials["MTLS_CLIENT_KEY"])
            mtls_client_cert_filename = self.save_secret_to_file(ldap_credentials["MTLS_CLIENT_CERT"])
            logger.info("Saved secrets to tmp files")

            username = ldap_credentials["LDAP_USERNAME"]
            # Log username but mask the password
            logger.info(f"Using LDAP username: {username}")
            # Log password length for debugging without exposing the actual password
            password_length = len(ldap_credentials["PASSWORD"]) if "PASSWORD" in ldap_credentials else 0
            logger.info(f"Password length: {password_length} characters")

            if "LDAP_GATEWAY_URL" not in os.environ:
                logger.error("LDAP_GATEWAY_URL not in environment variables")
                raise HcwException(500, "LDAP_GATEWAY_URL not configured", "exception")
            ldap_url = os.environ["LDAP_GATEWAY_URL"]
            logger.info(f"Connecting to LDAP server URL: '{ldap_url}'")

            try:
                # Log TLS configuration details
                logger.info(f"TLS configuration: Using client cert file: {mtls_client_cert_filename}")
                logger.info(f"TLS configuration: Using client key file: {mtls_client_private_key_filename}")
                logger.info(f"TLS configuration: Using server cert file: {server_cert_filename}")
                logger.info("TLS configuration: Validation set to CERT_REQUIRED")
                tls = Tls(
                    local_private_key_file=mtls_client_private_key_filename,
                    local_certificate_file=mtls_client_cert_filename,
                    ca_certs_file=server_cert_filename,
                    validate=CERT_REQUIRED
                )
                logger.info("TLS configuration created")
                # Log server configuration
                logger.info(f"Creating Server object with URL: '{ldap_url}', use_ssl=True")
                server = Server(ldap_url, use_ssl=True, tls=tls)
                logger.info(f"LDAP server object created: {server}")

                # Log connection details
                logger.info(f"Creating Connection with user: '{username}', client_strategy=SAFE_SYNC")
                connection = Connection(server, user=username, password=ldap_credentials["PASSWORD"], client_strategy=SAFE_SYNC)
                logger.info(f"Connection object created: {connection}")
                logger.info("Attempting to bind to LDAP server")

                # Attempt to bind and log the result
                bound = connection.bind()
                logger.info(f"Bind result: {bound}, Details: {connection.result}")
                if not bound:
                    logger.error(f"Could not bind to LDAP server. Result: {connection.result}")
                    raise HcwException(500, f"Could not bind to LDAP server. Result: {connection.result}", "exception")

                logger.info("Successfully bound to LDAP server")
                self.bind_time = datetime.now()

                return connection
            except LDAPException as e:
                logger.error(f"LDAP Exception during connection: {e}")
                raise HcwException(500, f"Error connecting to LDAP: {e}", "exception", "Error connecting to LDAP")
        except HcwException as e:
            # Pass through HcwException without modification
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during LDAP connection: {e}")
            raise HcwException(500, f"Error connecting to LDAP: {e}", "exception", "Error connecting to LDAP")

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
            logger.info(f"Searching LDAP for nhsPerson with uid: {uid}")

            # Removed "nhsPrinOcc", "nhsRPSGB"  "nhsSiteNames", "nhsSiteCodes"
            return_attributes = ["uid", "Sn", "givenName", "nhsMiddleNames", "personalTitle", "nhsPersonStatus",
                                    "objectclass", "uniqueIdentifier", "nhsOrgOpenDate", "nhsIDCode", "o",
                                    "nhsBusinessFunctionsCodes", "nhsJobRole", "nhsJobRoleCode", "nhsBusinessFunctions",
                                    "nhsOrgCloseDate", "nhsGMC", "nhsGDP", "nhsGDC", "nhsRCN",
                                    "nhsNMC", "nhsConsultant", "nhsGMP", "nhsOcsPrCode"]
            search_base = f"uid={uid},ou=people,o=nhs"
            logger.info(f"Search base: {search_base}")
            logger.info(f"LDAP server URL being used: {self.connection.server.host}")
            logger.info(f"LDAP connection bound to: {self.connection.bound}")
            logger.info("Executing LDAP search")
            success, result, response, request = self.connection.search(search_base,
                                                                        "(objectclass=*)",
                                                                        attributes=return_attributes)
            logger.info(f"Received LDAP response, success: {success}, result: {result}")

            # Check for user not found (result code 32)
            if not success and result.get("result") == LdapErrorCode.NOT_FOUND:
                logger.error(f"User with id {uid} not found")
                raise HcwException(404, f"User with id {uid} not found", "unknown")

            # Check for other errors
            if not success:
                logger.error(f"Unknown error from LDAP request. Result: {result}")
                raise HcwException(500, f"Unknown error from LDAP request. Result: {result}", "exception",
                                    "Unknown error from LDAP request")

            logger.info("Processing LDAP response")
            practitioner = NhsPerson(self.get_nhs_person(response))
            logger.info(f"Found practitioner: {practitioner.uid}, {practitioner.given_name} {practitioner.sn}")
            org_persons = [NhsOrgPerson(r) for r in self.get_org_person(response)]
            logger.info(f"Found {len(org_persons)} organization persons")
            roles = [NhsOrgPersonRole(r) for r in self.get_org_roles(response)]
            logger.info(f"Found {len(roles)} roles")

            active_roles = []
            for role in roles:
                if not role.role_stopped or role.role_stopped > datetime.now().date():
                    role.org_person = next(filter(lambda op: op.nhs_id_code == role.nhs_id_code, org_persons))
                    role.practitioner = practitioner
                    active_roles.append(role)
            logger.info(f"Found {len(active_roles)} active roles")
            return practitioner, org_persons, active_roles

        except LDAPException as e:
            logger.error(f"LDAP Exception during search: {e}")
            if allow_retry:
                logger.warning(f"Got an LDAP connection error {e}. Attempting to reconnect.")
                self.connection = self.connect()
                logger.info("LDAP connection re-established")
                return self.search_active_nhs_person(uid, allow_retry=False)
            else:
                logger.error(f"LDAP connection error and retry failed: {e}")
                raise HcwException(500, f"LDAP connection error and retry failed {e}", "exception","Error connecting to LDAP")
        except HcwException as e:
            # Pass through HcwException without modification
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during LDAP search: {e}")
            raise HcwException(500, f"Unexpected error during LDAP search: {e}", "exception", "Error during LDAP search")
