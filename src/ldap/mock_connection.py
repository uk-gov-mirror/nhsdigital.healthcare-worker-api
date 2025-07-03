"""
The MockHcwLdapConnection class contains hardcoded data to return when in sandbox mode. This is instead of the
real ldaps connection so we have no chance of returning PID from the LDAPS instance.
"""

from ldap.connection import HcwLdapConnection
from ldap.nhs_person import NhsPerson, NhsOrgPerson, NhsOrgPersonRole


class MockHcwLdapConnection(HcwLdapConnection):
    def search_active_nhs_person(self, uid: str) -> [NhsPerson, list[NhsOrgPerson], list[NhsOrgPersonRole]]:
        return NhsPerson({
            "uid": "123",
            "sn": "Westbrook",
            "givenName": "Tabby",
            "nhsMiddleNames": "Ashlyn",
            "personalTitle": "Mrs",
            "nhsPersonStatus": "1",
        }), [], []

    def search_org_roles(self, uid: str) -> list[NhsOrgPersonRole]:
        return []
