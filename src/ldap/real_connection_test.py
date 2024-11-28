import json
import os
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
    def test_search(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = [{"attributes": {
                "uid": ["123"],
                "sn": ["Smith"],
                "givenName": ["John"],
                "nhsMiddleNames": ["Doe James Dave"],
                "personalTitle": ["Mr"],
                "nhsPersonStatus": "1",
            }}]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            result = conn.search_active_nhs_person("123")

            expected_attributes = ["uid", "Sn", "givenName", "nhsMiddleNames", "personalTitle", "nhsPersonStatus"]
            connection.return_value.search.assert_called_with("uid=123,ou=people,o=nhs", "(objectclass=nhsPerson)",
                                                                attributes=expected_attributes)

            assert result.uid == "123"
            assert result.sn == "Smith"
            assert result.given_name == "John"
            assert result.nhs_middle_names == "Doe James Dave"
            assert result.personal_title == "Mr"
            assert result.nhs_person_status == "1"

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

    def test_search_multiple_matches(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = {"attributes": {
                "uid": ["123"],
                "sn": ["Smith"],
                "givenName": ["John"],
                "nhsMiddleNames": [],
                "personalTitle": ["Mr"],
                "nhsPersonStatus": "1",
            }}
            connection.return_value.search.return_value = True, {"result": 0}, [ldap_result, ldap_result], ""

            with pytest.raises(HcwException) as e:
                conn.search_active_nhs_person("123")

            assert e.value.status_code == 500
            assert e.value.return_message == "Found multiple users with id 123"

    def test_search_missing_values(self):
        boto3, _, _, connection, _ = setup_ldap_connection_mock()

        with patch.dict(os.environ, environment_variables()):
            mock_secrets(boto3)
            conn = RealHcwLdapConnection()

            ldap_result = [{"attributes": {
                "uid": [],
                "sn": [],
                "givenName": [],
                "nhsMiddleNames": [],
                "personalTitle": [],
                "nhsPersonStatus": "",
            }}]
            connection.return_value.search.return_value = True, {"result": 0}, ldap_result, ""

            result = conn.search_active_nhs_person("123")

            assert result.uid == ""
            assert result.sn == ""
            assert result.given_name == ""
            assert result.nhs_middle_names == ""
            assert result.personal_title == ""
            assert result.nhs_person_status == ""

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
