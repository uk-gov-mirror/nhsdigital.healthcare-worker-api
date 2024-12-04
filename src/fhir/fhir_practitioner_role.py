from fhir.fhir_codeable_concept import FhirCodeableConcept
from fhir.fhir_object import FhirObject
from fhir.fhir_organisation import FhirOrganisation
from fhir.fhir_period import FhirPeriod
from fhir.fhir_reference import FhirReference
from fhir.fhir_practitioner import FhirIdentifier, FhirPractitioner
from ldap.nhs_person import NhsOrgPersonRole


class FhirPractitionerRole(FhirObject):
    id: str
    identifier: [FhirIdentifier]
    code: [FhirCodeableConcept]
    active: bool
    period: FhirPeriod
    practitioner: FhirReference[FhirPractitioner]
    organization: FhirReference[FhirOrganisation]

    def __init__(self, practitioner_role: NhsOrgPersonRole):
        super().__init__("PractitionerRole")

        self.id = practitioner_role.profile_id
        self.identifier = [FhirIdentifier("https://fhir.nhs.uk/Id/sds-role-profile-id", practitioner_role.profile_id)]
        # TODO: Filter based on active flag
        self.active = True
        self.practitioner = FhirReference(FhirPractitioner(practitioner_role.practitioner))
        self.organization = FhirReference(FhirOrganisation(practitioner_role.org_person))

        self.period = FhirPeriod(practitioner_role.role_granted, practitioner_role.role_stopped)

        code = practitioner_role.job_role_code
        name = practitioner_role.job_role
        self.code = [FhirCodeableConcept("https://fhir.nhs.uk/CodeSystem/NHSDigital-SDS-JobRoleCode", code, name)]

    def __eq__(self, other: 'FhirPractitionerRole') -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
