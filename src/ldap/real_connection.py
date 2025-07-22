import json
import os
import socket
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

        # Add network diagnostics
        self.log_network_info()

        # Time the boto3 client creation
        client_start = time.time()
        self.client = boto3.client("secretsmanager", config=Config(region_name="eu-west-2"))
        client_duration = time.time() - client_start
        logger.info(f"boto3 client creation took {client_duration:.2f}s", "BOTO3_CLIENT_TIMING", "null")

        # Run isolated Secrets Manager performance test
        self.test_secrets_manager_performance()

        # Time the connection establishment
        connect_start = time.time()
        self.connection = self.connect()
        connect_duration = time.time() - connect_start
        logger.info(f"LDAP connection establishment took {connect_duration:.2f}s", "LDAP_CONNECT_TIMING", "null")

        total_init_duration = time.time() - init_start_time
        logger.info(f"Total LDAP initialization took {total_init_duration:.2f}s", "LDAP_INIT_TOTAL_TIMING", "null")
        logger.info("LDAP connection established", "LDAP_CONN_SUCCESS", "null")

    def log_network_info(self):
        """Log network and environment information for diagnostics"""
        try:
            # Lambda environment info
            aws_region = os.environ.get('AWS_REGION', 'unknown')
            has_vpc_config = 'AWS_LAMBDA_VPC_CONFIG_SUBNET_IDS' in os.environ
            vpc_subnets = os.environ.get('AWS_LAMBDA_VPC_CONFIG_SUBNET_IDS', 'none')

            logger.info(f"AWS Region: {aws_region}, VPC enabled: {has_vpc_config}", "LAMBDA_ENV_INFO", "null")
            if has_vpc_config:
                logger.info(f"VPC Subnets: {vpc_subnets}", "LAMBDA_VPC_SUBNETS", "null")

            # Test DNS resolution for Secrets Manager
            try:
                secretsmanager_hostname = 'secretsmanager.eu-west-2.amazonaws.com'
                dns_start = time.time()
                secretsmanager_ip = socket.gethostbyname(secretsmanager_hostname)
                dns_duration = time.time() - dns_start

                logger.info(f"DNS resolution took {dns_duration:.3f}s", "DNS_TIMING", "null")
                logger.info(f"Secrets Manager resolves to: {secretsmanager_ip}", "DNS_RESOLUTION", "null")

                # Check if it's a private IP (VPC endpoint) or public IP
                is_private = secretsmanager_ip.startswith(('10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.', '192.168.'))
                connection_path = "VPC endpoint (private)" if is_private else "Public internet"
                logger.info(f"Connection path: {connection_path}", "CONNECTION_PATH", "null")

                # Check if we can reach the IP on port 443
                try:
                    sock_test_start = time.time()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((secretsmanager_ip, 443))
                    sock.close()
                    sock_test_duration = time.time() - sock_test_start

                    if result == 0:
                        logger.info(f"TCP connection to {secretsmanager_ip}:443 successful in {sock_test_duration:.3f}s", "TCP_CONNECTION_TEST", "null")
                    else:
                        logger.warning(f"TCP connection to {secretsmanager_ip}:443 failed (code: {result}) in {sock_test_duration:.3f}s", "TCP_CONNECTION_FAILED", "null")
                except Exception as e:
                    logger.warning(f"TCP connection test failed: {e}", "TCP_CONNECTION_ERROR", "null")

            except Exception as e:
                logger.error(f"DNS resolution failed: {e}", "DNS_ERROR", "null")

            # Check if we can describe VPC endpoints (to confirm permissions and VPC setup)
            try:
                ec2_client = boto3.client('ec2', region_name='eu-west-2')
                vpc_endpoint_start = time.time()
                response = ec2_client.describe_vpc_endpoints(
                    Filters=[
                        {'Name': 'service-name', 'Values': ['com.amazonaws.eu-west-2.secretsmanager']},
                        {'Name': 'state', 'Values': ['available']}
                    ]
                )
                vpc_endpoint_duration = time.time() - vpc_endpoint_start

                endpoint_count = len(response.get('VpcEndpoints', []))
                logger.info(f"Found {endpoint_count} Secrets Manager VPC endpoints (query took {vpc_endpoint_duration:.3f}s)", "VPC_ENDPOINT_COUNT", "null")

                if endpoint_count > 0:
                    endpoint = response['VpcEndpoints'][0]
                    logger.info(f"VPC endpoint state: {endpoint.get('State', 'unknown')}, DNS enabled: {endpoint.get('PrivateDnsEnabled', 'unknown')}", "VPC_ENDPOINT_STATE", "null")

            except Exception as e:
                logger.warning(f"Could not check VPC endpoints: {e}", "VPC_ENDPOINT_CHECK_ERROR", "null")

        except Exception as e:
            logger.error(f"Network diagnostics failed: {e}", "NETWORK_DIAGNOSTICS_ERROR", "null")

    def test_secrets_manager_performance(self):
        """Test Secrets Manager performance in isolation"""
        try:
            logger.info("Starting isolated Secrets Manager performance test", "SECRETS_PERF_TEST_START", "null")

            # Test 1: Simple list secrets call (should be very fast)
            list_start = time.time()
            try:
                list_response = self.client.list_secrets(MaxResults=1)
                list_duration = time.time() - list_start
                logger.info(f"list_secrets call took {list_duration:.3f}s", "SECRETS_LIST_TIMING", "null")
            except Exception as e:
                list_duration = time.time() - list_start
                logger.error(f"list_secrets failed after {list_duration:.3f}s: {e}", "SECRETS_LIST_ERROR", "null")

            # Test 2: Actual secret retrieval
            secret_id = os.environ.get("LDAP_CREDENTIALS_SECRET_ID", "")
            if secret_id:
                get_start = time.time()
                try:
                    get_response = self.client.get_secret_value(SecretId=secret_id)
                    get_duration = time.time() - get_start
                    logger.info(f"get_secret_value call took {get_duration:.3f}s", "SECRETS_GET_TIMING_ISOLATED", "null")

                    # Log metadata without exposing secret content
                    secret_size = len(get_response.get("SecretString", ""))
                    version_id = get_response.get("VersionId", "unknown")
                    logger.info(f"Secret metadata - Size: {secret_size} bytes, Version: {version_id}", "SECRETS_METADATA", "null")

                except Exception as e:
                    get_duration = time.time() - get_start
                    logger.error(f"get_secret_value failed after {get_duration:.3f}s: {e}", "SECRETS_GET_ERROR_ISOLATED", "null")

            logger.info("Completed isolated Secrets Manager performance test", "SECRETS_PERF_TEST_END", "null")

        except Exception as e:
            logger.error(f"Secrets Manager performance test failed: {e}", "SECRETS_PERF_TEST_FAILED", "null")

    def get_secret(self, secret_id) -> dict:
        logger.info(f"Requesting secret: {secret_id}", "SECRET_REQUEST_START", "null")

        call_start = time.time()
        try:
            response = self.client.get_secret_value(SecretId=secret_id)
            call_duration = time.time() - call_start

            logger.info(f"get_secret_value call took {call_duration:.2f}s", "SECRET_CALL_TIMING", "null")

            # Time the JSON parsing
            parse_start = time.time()
            result = json.loads(response["SecretString"])
            parse_duration = time.time() - parse_start

            logger.info(f"JSON parsing took {parse_duration:.2f}s", "SECRET_PARSE_TIMING", "null")

            # Log secret size (without exposing content)
            secret_size = len(response["SecretString"])
            logger.info(f"Secret size: {secret_size} bytes", "SECRET_SIZE_INFO", "null")

            return result

        except Exception as e:
            call_duration = time.time() - call_start
            logger.error(f"get_secret_value failed after {call_duration:.2f}s: {e}", "SECRET_CALL_ERROR", "null")
            raise

    @staticmethod
    def save_secret_to_file(secret: str) -> str:
        file_start = time.time()
        filename = f"/tmp/{uuid.uuid4()}.pem"  # NOSONAR python:S5443
        with open(filename, "w") as f:
            f.write(secret)
        file_duration = time.time() - file_start
        logger.info(f"File write took {file_duration:.2f}s, size: {len(secret)} bytes", "FILE_WRITE_TIMING", "null")
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
        server_cert_filename = self.save_secret_to_file(ldap_credentials["LDAP_SERVER_CERT"])
        mtls_client_private_key_filename = self.save_secret_to_file(ldap_credentials["MTLS_CLIENT_KEY"])
        mtls_client_cert_filename = self.save_secret_to_file(ldap_credentials["MTLS_CLIENT_CERT"])
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
