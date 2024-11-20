import os
from ssl import CERT_REQUIRED
from unittest.mock import patch, call, mock_open

from ldap3 import SAFE_SYNC, AUTO_BIND_TLS_BEFORE_BIND

from ldap.connection import HcwLdapConnection


@patch.dict(os.environ, {"LDAP_SERVER_CERT_ID": "cert_id",
                            "MTLS_CLIENT_KEY_ID": "client_key_id",
                            "MTLS_CLIENT_CERT_ID": "client_cert_id",
                            "LDAP_USERNAME": "username",
                            "LDAP_PASSWORD_ID": "password_id",
                            "LDAP_GW_URL": "gw_url"})
@patch("builtins.open", new_callable=mock_open, read_data="data")
@patch("ldap.connection.uuid")
@patch("ldap.connection.Connection")
@patch("ldap.connection.Server")
@patch("ldap.connection.Tls")
@patch("ldap.connection.boto3")
def test_connect(boto3, tls, server, connection, uuid, _):
    uuid.uuid4.return_value = "id"
    boto3.client.return_value.get_secret_value.return_value = {"SecretString": "secret"}

    conn = HcwLdapConnection()
    boto3.client.return_value.get_secret_value.assert_has_calls([
        call(SecretId="cert_id"),
        call(SecretId="client_key_id"),
        call(SecretId="client_cert_id"),
        call(SecretId="password_id")], any_order=True)

    tmp_filename = "/tmp/id.pem"
    tls.assert_called_with(
        local_private_key_file=tmp_filename,
        local_certificate_file=tmp_filename,
        ca_certs_file=tmp_filename,
        validate=CERT_REQUIRED)

    server.assert_called_with("gw_url",
        use_ssl=True, tls=tls.return_value)

    connection.assert_called_with(server.return_value, user="username", password="secret",
                                    client_strategy=SAFE_SYNC, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)

    assert conn.connection == connection.return_value


# TODO: HCW-22: Tests for unhappy paths
@patch.dict(os.environ, {"LDAP_SERVER_CERT_ID": "cert_id",
                            "MTLS_CLIENT_KEY_ID": "client_key_id",
                            "MTLS_CLIENT_CERT_ID": "client_cert_id",
                            "LDAP_USERNAME": "username",
                            "LDAP_PASSWORD_ID": "password_id",
                            "LDAP_GW_URL": "gw_url"})
@patch("builtins.open", new_callable=mock_open, read_data="data")
@patch("ldap.connection.Connection")
@patch("ldap.connection.Server")
@patch("ldap.connection.Tls")
@patch("ldap.connection.boto3")
def test_search(boto3, tls, server, connection, _):
    conn = HcwLdapConnection()

    ldap_result = [{"attributes": {
        "uid": ["123"],
        "sn": ["Smith"],
        "givenName": ["John"],
        "nhsMiddleNames": ["Doe", "James", "Dave"],
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

