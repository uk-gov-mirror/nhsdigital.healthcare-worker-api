from fhir.fhir_object import FhirObject


class FhirEntrySearch(FhirObject):
    mode: str

    def __init__(self, mode: str):
        super().__init__(None)
        self.mode = mode

    def __eq__(self, other) -> bool:
        return self.mode == other.mode

    def __hash__(self) -> int:
        return hash(self.mode)
