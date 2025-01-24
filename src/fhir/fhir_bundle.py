from fhir.fhir_bundle_entry import FhirBundleEntry
from fhir.fhir_link import FhirLink
from fhir.fhir_object import FhirObject


class FhirBundle(FhirObject):
    type: str
    total: int
    entry: [FhirBundleEntry]
    link: [FhirLink]

    def __init__(self, type: str, total: int, entry: [FhirBundleEntry], link: FhirLink):
        super().__init__("Bundle")
        self.type = type
        self.total = total
        self.entry = entry
        self.link = [link]

    def __eq__(self, other) -> bool:
        return self.type == other.type and self.total == other.total

    def __hash__(self) -> int:
        return hash((self.type, self.total))
