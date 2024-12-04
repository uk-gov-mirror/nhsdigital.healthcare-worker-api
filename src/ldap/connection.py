from abc import abstractmethod

from ldap.nhs_person import NhsPerson, NhsOrgPersonRole, NhsOrgPerson


class HcwLdapConnection:
    @abstractmethod
    def search_active_nhs_person(self, uid: str) -> [NhsPerson, list[NhsOrgPerson], list[NhsOrgPersonRole]]:
        pass

    @abstractmethod
    def search_org_roles(self, uid: str) -> list[NhsOrgPersonRole]:
        pass
