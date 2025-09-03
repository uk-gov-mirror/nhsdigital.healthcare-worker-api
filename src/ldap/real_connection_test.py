import json
import os
import tempfile
import urllib.error
from contextlib import contextmanager
from datetime import datetime, date
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

    @staticmethod
    @contextmanager
    def _mock_extension_request():
        """
        Context manager to reduce urllib.request.urlopen duplication flagged by SonarCloud.
        Provides a mocked urlopen for extension testing.
        """
        with patch('urllib.request.urlopen') as mock_urlopen:
            yield mock_urlopen

    @staticmethod
    def _get_standard_secret_data():
        """Standard LDAP secret data used across tests"""
        return {
            "LDAP_SERVER_CERT": "server_cert",
            "MTLS_CLIENT_KEY": "client_key",
            "MTLS_CLIENT_CERT": "client_cert",
            "LDAP_USERNAME": "username",
            "PASSWORD": "password"
        }

    @staticmethod
    def _setup_extension_success_mock(mock_urlopen, secret_data=None, use_secret_string=True):
        """Setup mock for successful extension call"""
        if secret_data is None:
            secret_data = TestGetSecret._get_standard_secret_data()

        mock_response = MagicMock()
        if use_secret_string:
            response_data = {"SecretString": json.dumps(secret_data)}
        else:
            response_data = secret_data

        mock_response.read.return_value.decode.return_value = json.dumps(response_data)
        mock_urlopen.return_value.__enter__.return_value = mock_response

    @staticmethod
    def _setup_extension_failure_mock(mock_urlopen, error):
        """Setup mock for extension failure"""
        mock_urlopen.side_effect = error

    @staticmethod
    def _create_isolated_connection(boto3_mock):
        """Create connection without full initialization for isolated testing"""
        conn = RealHcwLdapConnection.__new__(RealHcwLdapConnection)
        conn.client = boto3_mock.client.return_value
        return conn

    @staticmethod
    def _assert_extension_called_correctly(mock_urlopen, expected_secret_id, expected_token="test_token"):
        """Assert extension was called with correct parameters"""
        args, _ = mock_urlopen.call_args
        request = args[0]
        assert "localhost:2773/secretsmanager/get" in request.get_full_url()
        assert f"secretId={expected_secret_id}" in request.get_full_url()
        assert request.get_header('X-aws-parameters-secrets-token') == expected_token

    @staticmethod
    def _assert_standard_secret_result(result):
        """Assert result contains expected LDAP credentials"""
        assert result["LDAP_USERNAME"] == "username"
        assert result["PASSWORD"] == "password"

    @staticmethod
    def _assert_boto3_fallback_called(boto3_mock, secret_id="test_secret_id"):
        """Assert boto3 fallback was called correctly"""
        boto3_mock.client.return_value.get_secret_value.assert_called_with(SecretId=secret_id)

    def test_get_secret_extension_success(self):
        """Test successful secret retrieval via AWS Secrets Manager Extension"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            with self._mock_extension_request() as mock_urlopen:
                self._setup_extension_success_mock(mock_urlopen)

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                self._assert_extension_called_correctly(mock_urlopen, "test_secret_id")
                self._assert_standard_secret_result(result)

                # Verify boto3 was NOT called (extension succeeded)
                boto3.client.return_value.get_secret_value.assert_not_called()

    def test_get_secret_extension_success_direct_format(self):
        """Test extension returning secret directly (not wrapped in SecretString)"""
        _, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            with self._mock_extension_request() as mock_urlopen:
                self._setup_extension_success_mock(mock_urlopen, use_secret_string=False)

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                self._assert_standard_secret_result(result)

    def test_get_secret_extension_no_session_token(self):
        """Test extension fails when AWS_SESSION_TOKEN is missing, falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables(), clear=True):  # No AWS_SESSION_TOKEN
            mock_secrets(boto3)

            conn = RealHcwLdapConnection()
            result = conn.get_secret("test_secret_id")

            self._assert_boto3_fallback_called(boto3)
            self._assert_standard_secret_result(result)

    def test_get_secret_extension_http_error_fallback(self):
        """Test extension HTTP error falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            mock_secrets(boto3)

            with self._mock_extension_request() as mock_urlopen:
                self._setup_extension_failure_mock(
                    mock_urlopen,
                    urllib.error.HTTPError("http://localhost:2773", 500, "Internal Server Error", {}, None)
                )

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                self._assert_boto3_fallback_called(boto3)
                self._assert_standard_secret_result(result)

    def test_get_secret_extension_connection_error_fallback(self):
        """Test extension connection error falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            mock_secrets(boto3)

            with self._mock_extension_request() as mock_urlopen:
                self._setup_extension_failure_mock(mock_urlopen, urllib.error.URLError("Connection refused"))

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                self._assert_boto3_fallback_called(boto3)
                self._assert_standard_secret_result(result)

    def test_get_secret_extension_json_error_fallback(self):
        """Test extension JSON parsing error falls back to boto3"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            mock_secrets(boto3)

            with self._mock_extension_request() as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value.decode.return_value = "invalid json"
                mock_urlopen.return_value.__enter__.return_value = mock_response

                conn = RealHcwLdapConnection()
                result = conn.get_secret("test_secret_id")

                self._assert_boto3_fallback_called(boto3)
                self._assert_standard_secret_result(result)

    def test_get_secret_extension_and_boto3_both_fail(self):
        """Test both extension and boto3 failing raises exception"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            with self._mock_extension_request() as mock_urlopen:
                self._setup_extension_failure_mock(mock_urlopen, urllib.error.URLError("Extension failed"))

                # Mock boto3 failure
                boto3.client.return_value.get_secret_value.side_effect = Exception("Boto3 failed")

                conn = self._create_isolated_connection(boto3)

                with pytest.raises(Exception) as e:
                    conn.get_secret("test_secret_id")

                assert "Boto3 failed" in str(e.value)

    def test_get_secret_special_characters_in_secret_id(self):
        """Test secret ID with special characters gets properly URL encoded"""
        boto3, _, _, _, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, {"AWS_SESSION_TOKEN": "test_token", **environment_variables()}):
            with self._mock_extension_request() as mock_urlopen:
                self._setup_extension_success_mock(mock_urlopen)

                conn = self._create_isolated_connection(boto3)
                result = conn.get_secret("secret/with/special@chars")

                # Verify URL encoding
                args, _ = mock_urlopen.call_args
                request = args[0]
                assert "secret%2Fwith%2Fspecial%40chars" in request.get_full_url()

                self._assert_standard_secret_result(result)


def test_connect():
    boto3, tls, server, connection, uuid = setup_ldap_connection_mock()

    with patch.dict(os.environ, environment_variables()):
        uuid.uuid4.return_value = "id"
        mock_secrets(boto3)

        conn = RealHcwLdapConnection()
        boto3.client.return_value.get_secret_value.assert_called_with(SecretId="creds_secret_id")

        # With certificate caching, each cert type gets its own content-hash based filename (SHA-256)
        temp_dir = tempfile.gettempdir()
        server_cert_filename = os.path.join(temp_dir, "server_cert_566980437245.pem")
        client_key_filename = os.path.join(temp_dir, "client_key_d9ee725310e9.pem")
        client_cert_filename = os.path.join(temp_dir, "client_cert_563a137a6115.pem")

        tls.assert_called_with(
            local_private_key_file=client_key_filename,
            local_certificate_file=client_cert_filename,
            ca_certs_file=server_cert_filename,
            validate=CERT_REQUIRED)

        server.assert_called_with("gateway_url",
            use_ssl=True, tls=tls.return_value)

        connection.assert_called_with(server.return_value, user="username", password="password",
                                        client_strategy=SAFE_SYNC, receive_timeout=8, pool_keepalive=8)
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
        assert e.value.message == "LDAP connection failed after 3 attempts: Connection error"
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


class TestRoleFilteringWithMissingDates:
    """Test role filtering logic for roles with missing nhsOrgOpenDate"""

    base_person_response = {
        "attributes": {
            "objectClass": "nhsPerson",
            "uid": "123",
            "sn": "Smith",
            "givenName": "John"
        }
    }

    def create_role_response(self, open_date="", close_date=""):
        """Helper to create role response with specified dates"""
        return {
            "attributes": {
                "objectClass": "nhsOrgPersonRole",
                "uniqueIdentifier": "role123",
                "nhsOrgOpenDate": open_date,
                "nhsOrgCloseDate": close_date,
                "nhsJobRole": "Doctor",
                "nhsJobRoleCode": "DOC",
                "nhsIDCode": "Y51"
            }
        }

    def create_org_person_response(self):
        """Helper to create org person response"""
        return {
            "attributes": {
                "objectClass": "nhsOrgPerson",
                "uniqueIdentifier": "orgPerson123",
                "nhsOrgOpenDate": "20200101",
                "o": "Test Hospital",
                "nhsIDCode": "Y51"
            }
        }

    def test_scenario_1_missing_open_date_past_close_date(self):
        """Test Scenario 1: Missing open date + past close date → exclude role"""
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = [
                self.base_person_response,
                self.create_org_person_response(),
                self.create_role_response(open_date="", close_date="20200101")  # Past date
            ]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            practitioner, org_persons, roles = conn.search_active_nhs_person("123")

            assert practitioner is not None
            assert len(org_persons) == 1
            assert len(roles) == 0  # Role should be excluded

    def test_scenario_2_missing_open_date_future_close_date(self):
        """Test Scenario 2: Missing open date + future close date → include with logging"""
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = [
                self.base_person_response,
                self.create_org_person_response(),
                self.create_role_response(open_date="", close_date="20301231")  # Future date
            ]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            practitioner, org_persons, roles = conn.search_active_nhs_person("123")

            assert practitioner is not None
            assert len(org_persons) == 1
            assert len(roles) == 1  # Role should be included
            assert roles[0].role_granted is None
            assert roles[0].role_stopped == date(2030, 12, 31)

    def test_scenario_3_missing_both_dates(self):
        """Test Scenario 3: Missing both dates → include with warning"""
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = [
                self.base_person_response,
                self.create_org_person_response(),
                self.create_role_response(open_date="", close_date="")  # Both missing
            ]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            practitioner, org_persons, roles = conn.search_active_nhs_person("123")

            assert practitioner is not None
            assert len(org_persons) == 1
            assert len(roles) == 1  # Role should be included
            assert roles[0].role_granted is None
            assert roles[0].role_stopped is None

    def test_valid_dates_still_work(self):
        """Test that roles with valid dates continue to work as before"""
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = [
                self.base_person_response,
                self.create_org_person_response(),
                self.create_role_response(open_date="20200101", close_date="20301231")  # Valid dates
            ]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            practitioner, org_persons, roles = conn.search_active_nhs_person("123")

            assert practitioner is not None
            assert len(org_persons) == 1
            assert len(roles) == 1
            assert roles[0].role_granted == date(2020, 1, 1)
            assert roles[0].role_stopped == date(2030, 12, 31)

    def test_multiple_roles_mixed_scenarios(self):
        """Test multiple roles with different date scenarios"""
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            # Create multiple roles with different scenarios
            role1 = self.create_role_response(open_date="", close_date="20200101")  # Exclude
            role1["attributes"]["uniqueIdentifier"] = "role1"

            role2 = self.create_role_response(open_date="", close_date="20301231")  # Include
            role2["attributes"]["uniqueIdentifier"] = "role2"

            role3 = self.create_role_response(open_date="20200101", close_date="20301231")  # Include
            role3["attributes"]["uniqueIdentifier"] = "role3"

            ldap_result = [
                self.base_person_response,
                self.create_org_person_response(),
                role1, role2, role3
            ]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            practitioner, org_persons, roles = conn.search_active_nhs_person("123")

            assert practitioner is not None
            assert len(org_persons) == 1
            assert len(roles) == 2  # Only role2 and role3 should be included

            role_ids = [role.profile_id for role in roles]
            assert "role1" not in role_ids  # Excluded
            assert "role2" in role_ids      # Included
            assert "role3" in role_ids      # Included


def test_ldap_retry_logic():
    """Test LDAP connection retry logic with timeout and exponential backoff"""
    from ldap3.core.exceptions import LDAPException
    from unittest.mock import MagicMock
    boto3, tls, server, connection, uuid = setup_ldap_connection_mock()

    with patch.dict(os.environ, environment_variables()):
        mock_secrets(boto3)

        # Create separate mock connection instances for each attempt
        connection_attempts = [MagicMock(), MagicMock(), MagicMock()]

        # First two attempts fail with bind exceptions, third succeeds
        connection_attempts[0].bind.side_effect = LDAPException("Network timeout")
        connection_attempts[1].bind.side_effect = LDAPException("Connection refused")
        connection_attempts[2].bind.return_value = True

        # Mock Connection to return our prepared instances
        connection.side_effect = connection_attempts

        # Mock time.sleep to avoid actual delays in test
        with patch('time.sleep') as mock_sleep:
            conn = RealHcwLdapConnection()

            # Should have made 3 connection attempts
            assert connection.call_count == 3

            # Should have called sleep twice (between attempts)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)  # First backoff: 1 second
            mock_sleep.assert_any_call(2)  # Second backoff: 2 seconds

            # Verify timeout parameters are set correctly
            for call in connection.call_args_list:
                kwargs = call[1]
                assert kwargs['receive_timeout'] == 8
                assert kwargs['pool_keepalive'] == 8

            # Connection should succeed after 3 attempts - use the last successful one
            assert conn.connection == connection_attempts[2]


def test_certificate_caching_file_error():
    """Test certificate caching handles file creation errors gracefully."""
    from ldap.real_connection import RealHcwLdapConnection
    import os
    from unittest.mock import patch

    # Clear any existing cache
    RealHcwLdapConnection._cert_file_cache.clear()

    test_cert_content = "test_cert_data"

    # Mock open to raise OSError on first call only
    original_open = open
    call_count = 0

    def mock_open_func(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1 and "test_cert_" in str(args[0]):
            raise OSError("Permission denied")
        return original_open(*args, **kwargs)

    with patch('builtins.open', side_effect=mock_open_func):
        # Should handle the error and create fallback file
        filename = RealHcwLdapConnection.save_secret_to_file_cached(test_cert_content, "test_cert")

        # Should have created some kind of fallback file
        assert filename.startswith(tempfile.gettempdir())
        assert filename.endswith(".pem")

    # Clean up
    RealHcwLdapConnection._cert_file_cache.clear()
    try:
        os.unlink(filename)
    except OSError:
        pass  # File cleanup - ignore if already gone
