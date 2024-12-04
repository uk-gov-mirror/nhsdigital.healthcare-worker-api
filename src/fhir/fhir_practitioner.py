from fhir.fhir_name import FhirName
from fhir.fhir_reference import FhirIdentifier, FhirReferable


class FhirPractitioner(FhirReferable):
    id: str
    active: bool
    identifier: [FhirIdentifier]
    name: [FhirName]

    def __init__(self, nhs_person):
        super().__init__("Practitioner")

        self.id = nhs_person.uid
        self.active = True
        self.identifier = [FhirIdentifier("https://fhir.nhs.uk/Id/sds-user-id", nhs_person.uid)]
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
        return f"{self.name[0].prefix} {self.name[0].given} {self.name[0].family}".strip()
