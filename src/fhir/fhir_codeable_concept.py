from fhir.fhir_object import FhirObject


class FhirCoding(FhirObject):
    system: str
    code: str
    display: str

    def __init__(self, system: str, code: str, display: str):
        super().__init__("Coding")
        self.system = system
        self.code = code
        self.display = display

    def __eq__(self, other: 'FhirCoding') -> bool:
        return self.system == other.system and self.code == other.code and self.display == other.display

    def __hash__(self) -> int:
        return hash((self.system, self.code, self.display))


class FhirCodeableConcept(FhirObject):
    coding: FhirCoding

    def __init__(self, system: str, code: str, display: str):
        super().__init__("CodeableConcept")
        self.coding = FhirCoding(system, code, display)

    def __eq__(self, other: 'FhirCodeableConcept') -> bool:
        return other.coding == self.coding

    def __hash__(self) -> int:
        return hash(self.coding)


