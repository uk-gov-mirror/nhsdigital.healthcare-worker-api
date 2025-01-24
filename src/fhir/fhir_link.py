from fhir.fhir_object import FhirObject


class FhirLink(FhirObject):
    relation: str
    url: str

    def __init__(self, relation: str, url: str):
        super().__init__(None)
        self.relation = relation
        self.url = url

    def __eq__(self, other) -> bool:
        return self.url == other.url

    def __hash__(self) -> int:
        return hash(self.url)
