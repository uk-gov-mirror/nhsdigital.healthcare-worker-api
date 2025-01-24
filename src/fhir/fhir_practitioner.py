import os
from typing import Optional

from fhir.fhir_name import FhirName
from fhir.fhir_object_with_url import FhirObjectWithUrl
from fhir.fhir_reference import FhirIdentifier, FhirReferable
from ldap.nhs_person import NhsPerson


def add_identifier(identifier_list: [FhirIdentifier], system: str, value: Optional[str]):
    if value:
        identifier_list.append(FhirIdentifier(system, value))

def get_identifiers(nhs_person: NhsPerson):
    identifiers = []

    add_identifier(identifiers, "https://fhir.nhs.uk/Id/sds-user-id", nhs_person.uid)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/rpsgb-membership-number", nhs_person.rpsgb_number)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/gmc-number", nhs_person.gmc_number)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/gdp-number", nhs_person.gdp_number)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/gdc-number", nhs_person.gdc_number)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/rcn-number", nhs_person.rcn_number)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/nmc-number", nhs_person.nmc_number)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/gmp-number", nhs_person.gmp_number)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/consultant-code", nhs_person.consultant_code)
    add_identifier(identifiers, "https://fhir.nhs.uk/Id/nacs-practitioner-code", nhs_person.nacs_practitioner_code)

    return identifiers


class FhirPractitioner(FhirReferable):
    id: str
    active: bool
    identifier: [FhirIdentifier]
    name: [FhirName]

    def __init__(self, nhs_person: NhsPerson):
        super().__init__("Practitioner")

        self.id = nhs_person.uid
        self.active = True
        self.identifier = get_identifiers(nhs_person)
        self.name = [FhirName(
            "usual",
            nhs_person.sn,
            f"{str(nhs_person.given_name or '')} {str(nhs_person.nhs_middle_names or '')}".strip(),
            nhs_person.personal_title
        )]

    def get_reference(self) -> str:
        return f"Practitioner/{self.id}"

    def get_identifier(self) -> FhirIdentifier:
        return FhirIdentifier("https://fhir.nhs.uk/Id/sds-user-id", self.id)

    def get_display(self) -> str:
        prefix_str = self.name[0].prefix[0] if hasattr(self.name[0], "prefix") else ""
        return f"{prefix_str} {self.name[0].given[0]} {self.name[0].family}".strip()
