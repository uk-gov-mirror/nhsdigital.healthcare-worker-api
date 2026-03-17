import os
from unittest.mock import patch

import pytest

import ldap.connection_fetch
from ldap.connection_fetch import get_connection


@pytest.fixture(autouse=True)
def tidy_up():
    yield

    ldap.connection_fetch.ldap_connection = None


@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_real_connection(connection_mock):
    connection = get_connection()
    assert connection == connection_mock.return_value


@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_real_connection_even_if_sandbox_mode_is_true(connection_mock):
    with patch.dict(os.environ, {"SANDBOX_MODE": "true"}):
        connection = get_connection()
    assert connection == connection_mock.return_value


@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_real_connection_with_unknown_value(connection_mock):
    with patch.dict(os.environ, {"SANDBOX_MODE": "non_boolean_value"}):
        connection = get_connection()
    assert connection == connection_mock.return_value


@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_real_connection_with_no_value(connection_mock):
    connection = get_connection()
    assert connection == connection_mock.return_value

