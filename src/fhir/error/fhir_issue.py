from fhir.fhir_codeable_concept import FhirCodeableConcept
from fhir.fhir_object import FhirObject


class FhirIssue(FhirObject):
    severity: str
    code: str
    details: FhirCodeableConcept

    def __init__(self, severity: str, code: str, details: FhirCodeableConcept):
        super().__init__(None)
        self.severity = severity
        self.code = code
        self.details = details

    def __eq__(self, other: 'FhirIssue') -> bool:
        return self.severity == other.severity and self.code == other.code and self.details == other.details

    def __hash__(self) -> int:
        return hash((self.severity, self.code, self.details))
