from fhir.fhir_object_with_url import FhirObjectWithUrl


class FhirStatus(FhirObjectWithUrl):
    ok: bool

    def __init__(self, ok: bool):
        super().__init__("Status")
        self.ok = ok

    def __eq__(self, other: 'FhirStatus') -> bool:
        return self.ok == other.ok

    def __hash__(self) -> int:
        return hash(self.ok)

    @property
    def url(self):
        return None
