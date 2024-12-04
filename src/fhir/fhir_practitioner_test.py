from unittest.mock import MagicMock

import jsonpickle

from fhir.fhir_practitioner import FhirPractitioner, FhirIdentifier, FhirName
from ldap.nhs_person import NhsPerson


# JSON serialisation is key to how this information is returned, and we are relying on a pip dependency to serialise
# the structure with embedded lists. In the future if this is time-consuming to maintain and we have proven faith
# in the jsonpickle package, then we might want to remove this test.
def test_fhir_worker_serialisation():
    nhs_person = MagicMock()
    nhs_person.uid = "uid"
    nhs_person.given_name = "Given"
    nhs_person.nhs_middle_names = "Middle"
    nhs_person.sn = "Family"
    nhs_person.personal_title = "Mr"

    worker = FhirPractitioner(nhs_person)

    serialised = jsonpickle.encode(worker, unpicklable=False)

    assert serialised == ('{"resourceType": "Practitioner", "id": "uid", "active": true, "identifier": '
                            '[{"resourceType": "Identifier", "system": "https://fhir.nhs.uk/Id/sds-user-id", "value": "uid"}], "name": '
                            '[{"resourceType": "Name", "use": "usual", "family": "Family", '
                            '"given": "Given Middle", "prefix": "Mr"}]}')

