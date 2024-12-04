from abc import abstractmethod

from fhir.fhir_object import FhirObject


class FhirIdentifier(FhirObject):
    system: str
    value: str

    def __init__(self, system: str, value: str):
        super().__init__("Identifier")

        self.system = system
        self.value = value

    def __eq__(self, other: "FhirIdentifier") -> bool:
        return self.system == other.system and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.system, self.value))


class FhirReferable(FhirObject):
    @abstractmethod
    def get_reference(self) -> str:
        pass

    @abstractmethod
    def get_identifier(self) -> FhirIdentifier:
        pass

    @abstractmethod
    def get_display(self) -> str:
        pass

    def __eq__(self, other: "FhirReferable") -> bool:
        return self.get_identifier() == other.get_identifier()

    def __hash__(self) -> int:
        return hash(self.get_identifier())


class FhirReference[T: FhirReferable](FhirObject):
    reference: str
    identifier: FhirIdentifier
    display: str
    full_value: T

    def __init__(self, value: T):
        super().__init__("Reference")

        self.reference = value.get_reference()
        self.identifier = value.get_identifier()
        self.display = value.get_display()
        self.full_value = value

    def __getstate__(self) -> dict:
        # Don't include the full value in json serialisation
        dict_copy = self.__dict__.copy()
        del dict_copy["full_value"]
        return dict_copy

    def __eq__(self, other: 'FhirReference') -> bool:
        return self.identifier == other.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)
