from abc import abstractmethod

from fhir.fhir_object import FhirObject


class FhirObjectWithUrl(FhirObject):
    @property
    @abstractmethod
    def url(self):
        pass
