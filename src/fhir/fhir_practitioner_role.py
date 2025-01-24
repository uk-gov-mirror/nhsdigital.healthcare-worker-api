import os

from fhir.fhir_codeable_concept import FhirCodeableConcept
from fhir.fhir_location import FhirLocation
from fhir.fhir_object import FhirObject
from fhir.fhir_object_with_url import FhirObjectWithUrl
from fhir.fhir_organisation import FhirOrganisation
from fhir.fhir_period import FhirPeriod
from fhir.fhir_reference import FhirReference
from fhir.fhir_practitioner import FhirIdentifier, FhirPractitioner
from ldap.nhs_person import NhsOrgPersonRole, NhsPerson


def get_locations(practitioner_role: NhsOrgPersonRole):
    if not practitioner_role or not practitioner_role.nacs_site_codes or not practitioner_role.nacs_site_names:
        return []

    site_count = min(len(practitioner_role.nacs_site_names), len(practitioner_role.nacs_site_codes))

    locations = []
    for i in range(0, site_count):
        locations.append(FhirReference(FhirLocation(practitioner_role.nacs_site_names[i], practitioner_role.nacs_site_codes[i])))

    if locations:
        return locations

    return None


class FhirPractitionerRole(FhirObjectWithUrl):
    id: str
    identifier: [FhirIdentifier]
    code: [FhirCodeableConcept]
    specialty: [FhirCodeableConcept]
    active: bool
    period: FhirPeriod
    location: [FhirReference[FhirLocation]]
    practitioner: FhirReference[FhirPractitioner]
    organization: FhirReference[FhirOrganisation]

    def __init__(self, practitioner: NhsPerson, practitioner_role: NhsOrgPersonRole):
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

        if practitioner.speciality:
            self.specialty = [FhirCodeableConcept("https://fhir.nhs.uk/CodeSystem/STU3/CodeSystem/Specialty-1", practitioner.speciality, practitioner.speciality)]

        locations = get_locations(practitioner_role)
        if locations:
            self.location = locations

    def __eq__(self, other: 'FhirPractitionerRole') -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def url(self):
        base_url = os.environ["BASE_URL"]
        return f"{base_url}PractitionerRole/{self.id}"
