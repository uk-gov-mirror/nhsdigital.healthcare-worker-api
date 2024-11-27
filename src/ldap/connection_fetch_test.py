import os
from unittest.mock import patch

import pytest

import ldap.connection_fetch
from ldap.connection_fetch import get_connection
from ldap.mock_connection import MockHcwLdapConnection


@pytest.fixture(autouse=True)
def tidy_up():
    yield

    ldap.connection_fetch.ldap_connection = None


@patch.dict(os.environ, {"SANDBOX_MODE": "true"})
def test_sandbox_connection():
    connection = get_connection()
    assert isinstance(connection, MockHcwLdapConnection)


@patch.dict(os.environ, {"SANDBOX_MODE": "false"})
@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_real_connection(connection_mock):
    connection = get_connection()
    assert connection == connection_mock.return_value


@patch.dict(os.environ, {"SANDBOX_MODE": "non_boolean_value"})
@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_real_connection_with_unknown_value(connection_mock):
    connection = get_connection()
    assert connection == connection_mock.return_value


@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_real_connection_with_no_value(connection_mock):
    connection = get_connection()
    assert connection == connection_mock.return_value

