from fhir.fhir_object import FhirObject


class FhirName(FhirObject):
    use: str
    family: str
    given: [str]
    prefix: [str]

    def __init__(self, use: str, family: str, given: str, prefix: str):
        super().__init__(None)
        self.use = use
        self.family = family
        self.given = [given]

        if prefix:
            self.prefix = [prefix]

    def __eq__(self, other: 'FhirName') -> bool:
        prefix_matches = other.prefix == self.prefix if hasattr(self, "prefix") else True
        return other.use == self.use and other.family == self.family and other.given == self.given and prefix_matches

    def __hash__(self) -> int:
        return hash((self.use, self.family, self.given, self.prefix))
