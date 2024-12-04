from fhir.fhir_reference import FhirReferable, FhirIdentifier
from ldap.nhs_person import NhsOrgPerson


class FhirOrganisation(FhirReferable):
    identifier: str
    name: str

    def __init__(self, org_person: NhsOrgPerson):
        super().__init__("Organisation")
        self.identifier = org_person.nhs_id_code
        self.name = org_person.org_name

    def get_reference(self) -> str:
        return f"Organisation/{self.identifier}"

    def get_identifier(self) -> FhirIdentifier:
        return FhirIdentifier("https://fhir.nhs.uk/Id/ods-organization-code", self.identifier)

    def get_display(self) -> str:
        return self.name
