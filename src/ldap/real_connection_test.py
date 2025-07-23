import json
import os
import urllib.error
from datetime import datetime
from ssl import CERT_REQUIRED
from unittest.mock import patch, mock_open, MagicMock

import pytest
from ldap3 import SAFE_SYNC, AUTO_BIND_TLS_BEFORE_BIND
from ldap3.core.exceptions import LDAPException

import ldap.real_connection
import builtins

from hcw_exception import HcwException
from ldap.real_connection import RealHcwLdapConnection


@pytest.fixture(autouse=True)
def cleanup():
    yield
    ldap.real_connection.connection = None


def environment_variables() -> dict:
    return {"LDAP_CREDENTIALS_SECRET_ID": "creds_secret_id",
            "LDAP_GATEWAY_URL": "gateway_url"}


def mock_secrets(boto3):
    boto3.client.return_value.get_secret_value.return_value = {"SecretString": json.dumps({
        "LDAP_SERVER_CERT": "server_cert",
        "MTLS_CLIENT_KEY": "client_key",
        "MTLS_CLIENT_CERT": "client_cert",
        "LDAP_USERNAME": "username",
        "PASSWORD": "password"
    })}


def setup_ldap_connection_mock():
    ldap.real_connection.boto3 = MagicMock()
    ldap.real_connection.Tls = MagicMock()
    ldap.real_connection.Server = MagicMock()
    ldap.real_connection.Connection = MagicMock()
    ldap.real_connection.uuid = MagicMock()
    builtins.open = mock_open()

    return (ldap.real_connection.boto3, ldap.real_connection.Tls, ldap.real_connection.Server,
            ldap.real_connection.Connection, ldap.real_connection.uuid)


class TestGetSecret:
    """Test the new AWS Secrets Manager Extension functionality"""

    def test_get_secret_extension_success(self):
        """Test successful secret retrieval via AWS Secrets Manager Extension"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            # Mock the extension HTTP call
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value.decode.return_value = json.dumps({
                    "SecretString": json.dumps({
                        "LDAP_SERVER_CERT": "server_cert",
                        "MTLS_CLIENT_KEY": "client_key",
                        "MTLS_CLIENT_CERT": "client_cert",
                        "LDAP_USERNAME": "username",
                        "PASSWORD": "password"
                    })
                })
                mock_urlopen.return_value.__enter__.return_value = mock_response

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                # Verify extension was called with correct URL and headers
                args, kwargs = mock_urlopen.call_args
                request = args[0]
                assert "localhost:2773/secretsmanager/get" in request.get_full_url()
                assert "secretId=test_secret_id" in request.get_full_url()
                assert request.get_header('X-aws-parameters-secrets-token') == "test_token"

                # Verify result
                assert result["LDAP_USERNAME"] == "username"
                assert result["PASSWORD"] == "password"

                # Verify boto3 was NOT called (extension succeeded)
                boto3.client.return_value.get_secret_value.assert_not_called()

    def test_get_secret_extension_success_direct_format(self):
        """Test extension returning secret directly (not wrapped in SecretString)"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            with patch('urllib.request.urlopen') as mock_urlopen:
                # Extension returns secret directly without SecretString wrapper
                mock_response = MagicMock()
                mock_response.read.return_value.decode.return_value = json.dumps({
                    "LDAP_SERVER_CERT": "server_cert",
                    "MTLS_CLIENT_KEY": "client_key",
                    "MTLS_CLIENT_CERT": "client_cert",
                    "LDAP_USERNAME": "username",
                    "PASSWORD": "password"
                })
                mock_urlopen.return_value.__enter__.return_value = mock_response

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                assert result["LDAP_USERNAME"] == "username"
                assert result["PASSWORD"] == "password"

    def test_get_secret_extension_no_session_token(self):
        """Test extension fails when AWS_SESSION_TOKEN is missing, falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables(), clear=True):  # No AWS_SESSION_TOKEN
            mock_secrets(boto3)

            conn = RealHcwLdapConnection()
            result = conn.get_secret("test_secret_id")

            # Should fall back to boto3
            boto3.client.return_value.get_secret_value.assert_called_with(SecretId="test_secret_id")
            assert result["LDAP_USERNAME"] == "username"

    def test_get_secret_extension_http_error_fallback(self):
        """Test extension HTTP error falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            mock_secrets(boto3)

            # Mock extension HTTP error
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = urllib.error.HTTPError(
                    "http://localhost:2773", 500, "Internal Server Error", {}, None
                )

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                # Should fall back to boto3
                boto3.client.return_value.get_secret_value.assert_called_with(SecretId="test_secret_id")
                assert result["LDAP_USERNAME"] == "username"

    def test_get_secret_extension_connection_error_fallback(self):
        """Test extension connection error falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            mock_secrets(boto3)

            # Mock extension connection error
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                # Should fall back to boto3
                boto3.client.return_value.get_secret_value.assert_called_with(SecretId="test_secret_id")
                assert result["LDAP_USERNAME"] == "username"

    def test_get_secret_extension_json_error_fallback(self):
        """Test extension JSON parsing error falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            mock_secrets(boto3)

            # Mock extension returning invalid JSON
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value.decode.return_value = "invalid json"
                mock_urlopen.return_value.__enter__.return_value = mock_response

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                # Should fall back to boto3
                boto3.client.return_value.get_secret_value.assert_called_with(SecretId="test_secret_id")
                assert result["LDAP_USERNAME"] == "username"

    def test_get_secret_extension_and_boto3_both_fail(self):
        """Test both extension and boto3 failing raises exception"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            # Mock extension failure
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = urllib.error.URLError("Extension failed")

                # Mock boto3 failure
                boto3.client.return_value.get_secret_value.side_effect = Exception("Boto3 failed")

                # Create connection without calling connect() to test get_secret in isolation
                conn = RealHcwLdapConnection.__new__(RealHcwLdapConnection)
                conn.client = boto3.client.return_value

                with pytest.raises(Exception) as e:
                    conn.get_secret("test_secret_id")

                assert "Boto3 failed" in str(e.value)

    def test_get_secret_special_characters_in_secret_id(self):
        """Test secret ID with special characters gets properly URL encoded"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value.decode.return_value = json.dumps({
                    "SecretString": json.dumps({
                        "LDAP_SERVER_CERT": "server_cert",
                        "MTLS_CLIENT_KEY": "client_key",
                        "MTLS_CLIENT_CERT": "client_cert",
                        "LDAP_USERNAME": "username",
                        "PASSWORD": "password"
                    })
                })
                mock_urlopen.return_value.__enter__.return_value = mock_response

                # Create connection without calling connect() to test get_secret in isolation
                conn = RealHcwLdapConnection.__new__(RealHcwLdapConnection)
                conn.client = boto3.client.return_value

                result = conn.get_secret("secret/with/special@chars")

                # Verify URL encoding
                args, kwargs = mock_urlopen.call_args
                request = args[0]
                assert "secret%2Fwith%2Fspecial%40chars" in request.get_full_url()

                # Verify result
                assert result["LDAP_USERNAME"] == "username"


def test_connect():
    boto3, tls, server, connection, uuid = setup_ldap_connection_mock()

    with patch.dict(os.environ, environment_variables()):
        uuid.uuid4.return_value = "id"
        mock_secrets(boto3)

        conn = RealHcwLdapConnection()
        boto3.client.return_value.get_secret_value.assert_called_with(SecretId="creds_secret_id")

        tmp_filename = "/tmp/id.pem"
        tls.assert_called_with(
            local_private_key_file=tmp_filename,
            local_certificate_file=tmp_filename,
            ca_certs_file=tmp_filename,
            validate=CERT_REQUIRED)

        server.assert_called_with("gateway_url",
            use_ssl=True, tls=tls.return_value)

        connection.assert_called_with(server.return_value, user="username", password="password",
                                        client_strategy=SAFE_SYNC)
        assert connection.return_value.bind.called

        assert conn.connection == connection.return_value


def test_connect_fail():
    boto3, _, _, connection, _ = setup_ldap_connection_mock()

    with patch.dict(os.environ, environment_variables()):
        mock_secrets(boto3)

        connection.side_effect = LDAPException("Connection error")

        with pytest.raises(HcwException) as e:
            RealHcwLdapConnection()

        assert e.value.status_code == 500
        assert e.value.message == "Error connecting to LDAP: Connection error"
        assert e.value.return_message == "Error connecting to LDAP"


class TestLdapSearch:
    full_ldap_response_example = [{
            "attributes": {
                "objectClass": ["nhsPerson"],
                "uid": ["123"],
                "sn": ["Smith"],
                "givenName": ["John"],
                "nhsMiddleNames": ["Doe James Dave"],
                "personalTitle": ["Mr"],
                "nhsPersonStatus": "1",
            }
        }, {
            "attributes": {
                "objectClass": ["nhsOrgPerson"],
                "uniqueIdentifier": "orgPersonId",
                "nhsOrgOpenDate": "20240101",
                "o": "org",
                "nhsIDCode": "Y51"
            }
        }, {
            "attributes": {
                "objectClass": ["nhsOrgPersonRole"],
                "uniqueIdentifier": "orgPersonRoleId",
                "nhsBusinessFunctionsCodes": "bCodes",
                "nhsBusinessFunctions": "bFunctions",
                "nhsJobRole": "jobRole",
                "nhsJobRoleCode": "jobRoleCode",
                "nhsIDCode": "Y51",
                "nhsOrgOpenDate": "20200101",
                "nhsOrgCloseDate": "29990101",
            }
        }]

    def test_search(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            connection.return_value.search.return_value = True, {"result": 0}, self.full_ldap_response_example, ""

            practitioner, org_persons, roles = conn.search_active_nhs_person("123")

            expected_attributes = ["uid", "Sn", "givenName", "nhsMiddleNames", "personalTitle", "nhsPersonStatus",
                                    "objectclass", "uniqueIdentifier", "nhsOrgOpenDate", "nhsIDCode", "o",
                                    "nhsBusinessFunctionsCodes", "nhsJobRole", "nhsJobRoleCode", "nhsBusinessFunctions",
                                    "nhsOrgCloseDate", "nhsGMC", "nhsGDP", "nhsGDC", "nhsRCN",
                                    "nhsNMC", "nhsConsultant", "nhsGMP", "nhsOcsPrCode"]
            connection.return_value.search.assert_called_with("uid=123,ou=people,o=nhs", "(objectclass=*)",
                                                                attributes=expected_attributes)

            assert practitioner.uid == "123"
            assert practitioner.sn == "Smith"
            assert practitioner.given_name == "John"
            assert practitioner.nhs_middle_names == "Doe James Dave"
            assert practitioner.personal_title == "Mr"
            assert practitioner.nhs_person_status == "1"

            assert len(org_persons) == 1
            assert org_persons[0].org_person_id == "orgPersonId"
            assert org_persons[0].joined == datetime(2024, 1, 1).date()
            assert org_persons[0].ods_code == "Y51"
            assert org_persons[0].org_name == "org"
            assert org_persons[0].nhs_id_code == "Y51"

            assert len(roles) == 1
            assert roles[0].profile_id == "orgPersonRoleId"
            assert roles[0].business_function_codes == "bCodes"
            assert roles[0].job_role == "jobRole"
            assert roles[0].job_role_code == "jobRoleCode"
            assert roles[0].role_granted == datetime(2020, 1, 1).date()
            assert roles[0].role_stopped == datetime(2999, 1, 1).date()
            assert roles[0].practitioner.uid == "123"
            assert roles[0].org_person.org_person_id == "orgPersonId"

    def test_search_person_not_found(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            connection.return_value.search.return_value = False, {"result": 32}, None, ""

            with pytest.raises(HcwException) as e:
                conn.search_active_nhs_person("123")

            assert e.value.status_code == 404
            assert e.value.message == "User with id 123 not found"

    def test_search_missing_values(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = [{"attributes": {
                "objectClass": "nhsPerson",
                "uid": [],
                "sn": [],
                "givenName": [],
                "nhsMiddleNames": [],
                "personalTitle": [],
                "nhsPersonStatus": "",
            }}]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            nhs_person, _org_persons, roles = conn.search_active_nhs_person("123")

            assert nhs_person.uid == ""
            assert nhs_person.sn == ""
            assert nhs_person.given_name == ""
            assert nhs_person.nhs_middle_names == ""
            assert nhs_person.personal_title == ""
            assert nhs_person.nhs_person_status == ""

    def test_search_returns_error(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            connection.return_value.search.return_value = False, {"result": 999}, None, ""

            with pytest.raises(HcwException) as e:
                conn.search_active_nhs_person("123")

            assert e.value.status_code == 500
            assert e.value.return_message == "Unknown error from LDAP request"

    def test_search_filters_inactive_roles(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            example = self.full_ldap_response_example.copy()
            example[2]["attributes"]["nhsOrgCloseDate"] = "20240501"  # Close date in the past
            connection.return_value.search.return_value = True, {"result": 0}, example, ""

            practitioner, org_persons, roles = conn.search_active_nhs_person("123")

            assert practitioner is not None
            assert len(org_persons) == 1
            assert roles == []
