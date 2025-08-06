import json
import os
import time
import uuid
import urllib.error
import hashlib
from datetime import datetime
from enum import IntEnum
from ssl import CERT_REQUIRED
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
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

    # Class-level cache for certificate files (persists across requests in warm container)
    _cert_file_cache = {}

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
        logger.info(f"LDAP connection establishment took {connect_duration:.2f}s", "LDAP_CONNECT_TIMING", "null")

        total_init_duration = time.time() - init_start_time
        logger.info(f"Total LDAP initialization took {total_init_duration:.2f}s", "LDAP_INIT_TOTAL_TIMING", "null")
        logger.info("LDAP connection established", "LDAP_CONN_SUCCESS", "null")

    def _make_extension_request(self, url: str, headers: dict, timeout: int = 5) -> dict:
        """
        Make HTTP request to AWS Secrets Manager Extension with proper error handling.
        Extracted to reduce code duplication flagged by SonarCloud.
        """
        import urllib.request

        request = urllib.request.Request(url)
        for header_name, header_value in headers.items():
            request.add_header(header_name, header_value)

        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_text = response.read().decode()
            return json.loads(response_text)

    def get_secret(self, secret_id) -> dict:
        logger.info(f"Requesting secret: {secret_id}", "SECRET_REQUEST_START", "null")

        # Try AWS Secrets Manager Extension first (localhost:2773)
        call_start = time.time()
        try:
            import urllib.parse

            # Get AWS session token for extension authentication
            aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
            if not aws_session_token:
                raise OSError("AWS_SESSION_TOKEN not available")

            # Extension HTTP API endpoint for Secrets Manager
            # Format: http://localhost:2773/secretsmanager/get?secretId=<secret-id>
            encoded_secret_id = urllib.parse.quote(secret_id, safe='')
            url = f"http://localhost:2773/secretsmanager/get?secretId={encoded_secret_id}"

            logger.info("Attempting AWS Secrets Manager Extension", "SECRET_EXTENSION_ATTEMPT", "null")

            # Use extracted method to make the HTTP request
            headers = {'X-Aws-Parameters-Secrets-Token': aws_session_token}
            extension_result = self._make_extension_request(url, headers)

            call_duration = time.time() - call_start
            logger.info(f"Extension call took {call_duration:.2f}s", "SECRET_EXTENSION_TIMING", "null")

            # The extension returns the secret in a different format
            # Extract the SecretString from the extension response
            if 'SecretString' in extension_result:
                secret_string = extension_result['SecretString']
            else:
                # Fallback: if the response format is different, log and fall back
                logger.info(f"Extension response format: {list(extension_result.keys())}", "SECRET_EXTENSION_FORMAT", "null")
                secret_string = extension_result

            # Parse the actual secret content
            parse_start = time.time()
            if isinstance(secret_string, str):
                result = json.loads(secret_string)
            else:
                result = secret_string
            parse_duration = time.time() - parse_start

            logger.info(f"JSON parsing took {parse_duration:.2f}s", "SECRET_PARSE_TIMING", "null")
            logger.info("Successfully used AWS Secrets Manager Extension", "SECRET_EXTENSION_SUCCESS", "null")

            return result

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
            call_duration = time.time() - call_start
            logger.info(f"Extension failed after {call_duration:.2f}s: {e}", "SECRET_EXTENSION_FAILED", "null")

            # Fall back to boto3
            logger.info("Falling back to boto3", "SECRET_BOTO3_FALLBACK", "null")

            fallback_start = time.time()
            try:
                response = self.client.get_secret_value(SecretId=secret_id)
                fallback_duration = time.time() - fallback_start

                logger.info(f"boto3 fallback call took {fallback_duration:.2f}s", "SECRET_BOTO3_TIMING", "null")

                # Time the JSON parsing
                parse_start = time.time()
                result = json.loads(response["SecretString"])
                parse_duration = time.time() - parse_start

                logger.info(f"JSON parsing took {parse_duration:.2f}s", "SECRET_PARSE_TIMING", "null")

                # Log secret size (without exposing content)
                secret_size = len(response["SecretString"])
                logger.info(f"Secret size: {secret_size} bytes", "SECRET_SIZE", "null")

                logger.info("Successfully fetched secret via boto3 fallback", "SECRET_BOTO3_SUCCESS", "null")
                return result

            except (json.JSONDecodeError, KeyError, ClientError, OSError) as boto_error:
                fallback_duration = time.time() - fallback_start
                logger.error(f"boto3 fallback also failed after {fallback_duration:.2f}s: {boto_error}", "SECRET_BOTO3_ERROR", "null")
                raise boto_error

    @classmethod
    def save_secret_to_file_cached(cls, secret: str, cert_type: str) -> str:
        """
        Cache certificate files to avoid redundant I/O operations.
        Uses content hash to identify unique certificates and reuse existing files.
        """
        file_start = time.time()

        # Generate content hash for cache key using SHA-256 (secure alternative to MD5)
        content_hash = hashlib.sha256(secret.encode()).hexdigest()[:12]  # 12 chars sufficient for uniqueness
        cache_key = f"{cert_type}_{content_hash}"

        # Check if we already have this certificate cached
        if cache_key in cls._cert_file_cache:
            cached_filename = cls._cert_file_cache[cache_key]
            # Verify file still exists (Lambda /tmp/ can be cleared)
            try:
                if os.path.exists(cached_filename):
                    file_duration = time.time() - file_start
                    logger.info(f"Certificate cache HIT for {cert_type}, took {file_duration:.3f}s", "CERT_CACHE_HIT", "null")
                    return cached_filename
                else:
                    # File was deleted, remove from cache
                    del cls._cert_file_cache[cache_key]
                    logger.info(f"Cached {cert_type} file was deleted, removing from cache", "CERT_CACHE_CLEANUP", "null")
            except OSError as check_error:
                # Handle case where file check fails (e.g., permission issues)
                logger.info(f"Cache file check failed for {cert_type}: {check_error}, removing from cache", "CERT_CACHE_CHECK_FAILED", "null")
                del cls._cert_file_cache[cache_key]

        # Cache miss - create new file with predictable name
        filename = f"/tmp/{cert_type}_{content_hash}.pem"  # NOSONAR python:S5443

        try:
            with open(filename, "w") as f:
                f.write(secret)

            # Store in cache for future use
            cls._cert_file_cache[cache_key] = filename
        except (OSError, IOError) as file_error:
            logger.error(f"Failed to create certificate file {filename}: {file_error}", "CERT_FILE_ERROR", "null")
            # Fallback: use temporary file with UUID (original behavior)
            fallback_filename = f"/tmp/{uuid.uuid4()}.pem"  # NOSONAR python:S5443
            with open(fallback_filename, "w") as f:
                f.write(secret)
            filename = fallback_filename
            logger.info(f"Created fallback certificate file: {filename}", "CERT_FALLBACK_FILE", "null")

        file_duration = time.time() - file_start
        logger.info(f"Certificate cache MISS for {cert_type}, created file, took {file_duration:.3f}s, size: {len(secret)} bytes", "CERT_CACHE_MISS", "null")

        return filename

    def connect(self) -> Optional[Connection]:
        connect_start_time = time.time()
        logger.info("About to fetch secrets", "SECRETS_CONN_START", "null")

        # Time the environment check
        env_check_start = time.time()
        if "LDAP_CREDENTIALS_SECRET_ID" not in os.environ:
            logger.error("Could not form LDAP connection","LDAP_CONN_ERROR", "null")
            return None
        env_check_duration = time.time() - env_check_start
        logger.info(f"Environment check took {env_check_duration:.2f}s", "ENV_CHECK_TIMING", "null")

        # Time the actual secret fetch
        secret_fetch_start = time.time()
        ldap_credentials = self.get_secret(os.environ["LDAP_CREDENTIALS_SECRET_ID"])
        secret_fetch_duration = time.time() - secret_fetch_start
        logger.info(f"Secret fetch took {secret_fetch_duration:.2f}s", "SECRET_FETCH_TIMING", "null")
        logger.info("Fetched secrets", "SECRETS_CONN_SUCCESS", "null")

        # Time the file operations
        file_ops_start = time.time()
        server_cert_filename = self.save_secret_to_file_cached(ldap_credentials["LDAP_SERVER_CERT"], "server_cert")
        mtls_client_private_key_filename = self.save_secret_to_file_cached(ldap_credentials["MTLS_CLIENT_KEY"], "client_key")
        mtls_client_cert_filename = self.save_secret_to_file_cached(ldap_credentials["MTLS_CLIENT_CERT"], "client_cert")
        file_ops_duration = time.time() - file_ops_start
        logger.info(f"All file operations took {file_ops_duration:.2f}s", "FILE_OPS_TIMING", "null")
        logger.info("Saved secrets to tmp file","SECRETS_TMP_FILE", "null")

        username = ldap_credentials["LDAP_USERNAME"]
        password = ldap_credentials["PASSWORD"]

        # Time the TLS and connection setup
        tls_setup_start = time.time()
        try:
            tls = Tls(
                local_private_key_file=mtls_client_private_key_filename,
                local_certificate_file=mtls_client_cert_filename,
                ca_certs_file=server_cert_filename,
                validate=CERT_REQUIRED
            )
            server = Server(os.environ["LDAP_GATEWAY_URL"], use_ssl=True, tls=tls)
            connection = Connection(server, user=username, password=password, client_strategy=SAFE_SYNC)
            tls_setup_duration = time.time() - tls_setup_start
            logger.info(f"TLS and server setup took {tls_setup_duration:.2f}s", "TLS_SETUP_TIMING", "null")

            # Time the actual bind operation
            bind_start = time.time()
            bound = connection.bind()
            bind_duration = time.time() - bind_start
            logger.info(f"LDAP bind operation took {bind_duration:.2f}s", "LDAP_BIND_TIMING", "null")

            if not bound:
                raise HcwException(500, "Could not bind to LDAP server", "exception")

            self.bind_time = datetime.now()

            total_connect_duration = time.time() - connect_start_time
            logger.info(f"Total connect() method took {total_connect_duration:.2f}s", "CONNECT_TOTAL_TIMING", "null")

            return connection
        except LDAPException as e:
            tls_setup_duration = time.time() - tls_setup_start
            logger.error(f"LDAP connection failed after {tls_setup_duration:.2f}s: {e}", "LDAP_CONNECT_ERROR", "null")
            raise HcwException(500, f"Error connecting to LDAP: {e}", "exception", "Error connecting to LDAP")

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
