from fhir.error.fhir_issue import FhirIssue
from fhir.fhir_object import FhirObject


class FhirOperationOutcome(FhirObject):
    issue: [FhirIssue]

    def __init__(self, issue: FhirIssue):
        super().__init__("OperationOutcome")
        self.issue = [issue]

    def __eq__(self, other) -> bool:
        return self.issue[0] == other.issue[0]

    def __hash__(self) -> int:
        return hash(self.issue[0])
