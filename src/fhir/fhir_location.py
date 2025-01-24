from fhir.fhir_reference import FhirReferable, FhirIdentifier


class FhirLocation(FhirReferable):
    display: str
    identifier: FhirIdentifier

    def __init__(self, site_name: str, site_code: str):
        super().__init__("Location")
        self.display = site_name
        self.identifier = FhirIdentifier("", site_code)

    def get_reference(self) -> str:
        return self.identifier.value

    def get_identifier(self) -> FhirIdentifier:
        return self.identifier

    def get_display(self) -> str:
        return self.display

