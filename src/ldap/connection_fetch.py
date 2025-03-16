import os
from datetime import datetime, timedelta
from typing import Optional

from ldap.connection import HcwLdapConnection
from ldap.mock_connection import MockHcwLdapConnection
from ldap.real_connection import RealHcwLdapConnection
from logs.log import Log

logger = Log("connection_fetch")

# Creating the connection here means that it's saved between requests, meaning that we don't need to re-establish
# the LDAP connection on every request.
ldap_connection: Optional[HcwLdapConnection] = None


def get_connection():
    global ldap_connection

    logger.info("get_connection called")
    
    # Check if we need a new connection
    if not ldap_connection:
        logger.info("No existing LDAP connection, creating new one")
    elif ldap_connection.connection.closed:
        logger.info("Existing LDAP connection is closed, creating new one")
    elif ldap_connection.bind_time < datetime.now() - timedelta(minutes=5):
        logger.info("Existing LDAP connection is older than 5 minutes, creating new one")
    else:
        logger.info("Using existing LDAP connection")
        return ldap_connection
    
    # Create a new connection
    logger.info("Creating new ldap connection instance")
    
    if "SANDBOX_MODE" in os.environ and os.environ["SANDBOX_MODE"].lower() == "true":
        logger.info("Using MockHcwLdapConnection (SANDBOX_MODE=true)")
        ldap_connection = MockHcwLdapConnection()
    else:
        logger.info("Using RealHcwLdapConnection")
        ldap_connection = RealHcwLdapConnection()

    return ldap_connection


# if "UNIT_TESTING" not in os.environ:
#     # Unfortunately doing this during unit testing is difficult because it triggers during the import before we have
#     # any mocking. But having it here moves the initial connection creation to the lambda start instead of the first
#     # request, which greatly improves performance for that request if we have provisioned concurrency.
#     ldap_connection = get_connection()
