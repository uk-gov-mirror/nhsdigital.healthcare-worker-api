from fhir.fhir_object import FhirObject


class FhirName(FhirObject):
    use: str
    family: str
    given: str
    prefix: str

    def __init__(self, use: str, family: str, given: str, prefix: str):
        super().__init__("Name")
        self.use = use
        self.family = family
        self.given = given
        self.prefix = prefix

    def __eq__(self, other: 'FhirName') -> bool:
        return (other.use == self.use and other.family == self.family and other.given == self.given and
                other.prefix == self.prefix)

    def __hash__(self) -> int:
        return hash((self.use, self.family, self.given, self.prefix))
