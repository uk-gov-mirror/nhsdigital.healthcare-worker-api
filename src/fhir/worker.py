import json

from fhir.fhir_object import FhirObject


class FhirIdentifier(FhirObject):
    system: str
    value: str

    def __init__(self, system: str, value: str):
        self.system = system
        self.value = value


class FhirName(FhirObject):
    use: str
    family: str
    given: str
    prefix: str

    def __init__(self, use: str, family: str, given: str, prefix: str):
        self.use = use
        self.family = family
        self.given = given
        self.prefix = prefix


class FhirWorker(FhirObject):
    id: str
    resourceType: str
    active: bool
    identifier: [FhirIdentifier]
    name: [FhirName]
