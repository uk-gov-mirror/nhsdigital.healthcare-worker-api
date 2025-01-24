from fhir.fhir_entry_search import FhirEntrySearch
from fhir.fhir_object import FhirObject
from fhir.fhir_object_with_url import FhirObjectWithUrl


class FhirBundleEntry(FhirObject):
    search: FhirEntrySearch
    resource: FhirObjectWithUrl
    fullUrl: str

    def __init__(self, search: FhirEntrySearch, resource: FhirObjectWithUrl):
        super().__init__(None)
        self.search = search
        self.resource = resource
        self.fullUrl = resource.url

    def __eq__(self, other: 'FhirBundleEntry') -> bool:
        return self.resource == other.resource

    def __hash__(self) -> int:
        return hash(self.resource)
