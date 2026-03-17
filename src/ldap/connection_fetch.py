from datetime import datetime, timedelta
from typing import Optional

from ldap.connection import HcwLdapConnection
from ldap.real_connection import RealHcwLdapConnection
from logs.log import Log

logger = Log("connection_fetch")

# Creating the connection here means that it's saved between requests, meaning that we don't need to re-establish
# the LDAP connection on every request.
ldap_connection: Optional[HcwLdapConnection] = None


def get_connection():
    global ldap_connection

    if (not ldap_connection or ldap_connection.connection.closed
            or ldap_connection.bind_time < datetime.now() - timedelta(minutes=5)):
        logger.info("Creating new real LDAP connection", "LDAP_CONN_REAL", "null")
        ldap_connection = RealHcwLdapConnection()

    return ldap_connection


# if "UNIT_TESTING" not in os.environ:
#     # Unfortunately doing this during unit testing is difficult because it triggers during the import before we have
#     # any mocking. But having it here moves the initial connection creation to the lambda start instead of the first
#     # request, which greatly improves performance for that request if we have provisioned concurrency.
#     ldap_connection = get_connection()
