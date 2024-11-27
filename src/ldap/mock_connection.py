"""
The MockHcwLdapConnection class contains hardcoded data to return when in sandbox mode. This is instead of the
real ldaps connection so we have no chance of returning PID from the LDAPS instance.
"""

from ldap.connection import HcwLdapConnection
from ldap.nhs_person import NhsPerson


class MockHcwLdapConnection(HcwLdapConnection):
    def search_active_nhs_person(self, uid: str) -> NhsPerson:
        return NhsPerson([123], ["Westbrook"], ["Tabby"], ["Ashlyn"], ["Mrs"], "1")
