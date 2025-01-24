from fhir.fhir_reference import FhirReferable, FhirIdentifier
from ldap.nhs_person import NhsOrgPerson


class FhirOrganisation(FhirReferable):
    id: str
    identifier: [FhirIdentifier]
    name: str

    def __init__(self, org_person: NhsOrgPerson):
        super().__init__("Organization")
        self.id = org_person.nhs_id_code
        self.identifier = [FhirIdentifier("https://fhir.nhs.uk/Id/ods-organization-code", org_person.nhs_id_code)]
        self.name = org_person.org_name

    def get_reference(self) -> str:
        return f"Organization/{self.id}"

    def get_identifier(self) -> FhirIdentifier:
        return self.identifier[0]

    def get_display(self) -> str:
        return self.name
