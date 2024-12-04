from fhir.fhir_object import FhirObject


class FhirStatus(FhirObject):
    ok: bool

    def __init__(self, ok: bool):
        super().__init__("Status")
        self.ok = ok

    def __eq__(self, other: 'FhirStatus') -> bool:
        return self.ok == other.ok

    def __hash__(self) -> int:
        return hash(self.ok)
