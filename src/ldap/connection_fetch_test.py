from datetime import datetime, timedelta
from types import SimpleNamespace
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
def test_reuses_existing_open_connection(connection_mock):
    existing_connection = SimpleNamespace(
        connection=SimpleNamespace(closed=False),
        bind_time=datetime.now(),
    )
    ldap.connection_fetch.ldap_connection = existing_connection

    connection = get_connection()

    assert connection == existing_connection
    connection_mock.assert_not_called()


@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_recreates_stale_connection(connection_mock):
    ldap.connection_fetch.ldap_connection = SimpleNamespace(
        connection=SimpleNamespace(closed=False),
        bind_time=datetime.now() - timedelta(minutes=6),
    )

    connection = get_connection()

    assert connection == connection_mock.return_value


@patch("ldap.connection_fetch.RealHcwLdapConnection")
def test_recreates_closed_connection(connection_mock):
    ldap.connection_fetch.ldap_connection = SimpleNamespace(
        connection=SimpleNamespace(closed=True),
        bind_time=datetime.now(),
    )

    connection = get_connection()

    assert connection == connection_mock.return_value

