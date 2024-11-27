from abc import abstractmethod

from ldap.nhs_person import NhsPerson


class HcwLdapConnection:
    @abstractmethod
    def search_active_nhs_person(self, uid: str) -> NhsPerson:
        pass
