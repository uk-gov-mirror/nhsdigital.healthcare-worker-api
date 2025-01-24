from abc import abstractmethod


class FhirObject:
    resourceType: str

    def __init__(self, resource_type: str | None):
        if resource_type:
            self.resourceType = resource_type

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass
