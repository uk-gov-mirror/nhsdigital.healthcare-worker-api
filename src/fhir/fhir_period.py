from datetime import date
from typing import Optional

from fhir.fhir_object import FhirObject


class FhirPeriod(FhirObject):
    start: str
    end: str

    def __init__(self, start: date, end: Optional[date]):
        super().__init__(None)
        self.start = start.strftime("%Y-%m-%d")
        if end:
            self.end = end.strftime("%Y-%m-%d")

    def __eq__(self, other: 'FhirPeriod') -> bool:
        return self.start == other.start and self.end == other.end

    def __hash__(self) -> int:
        return hash((self.start, self.end))
