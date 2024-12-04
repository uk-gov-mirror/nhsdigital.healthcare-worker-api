import jsonpickle

from fhir.fhir_practitioner import FhirPractitioner
from fhir.fhir_reference import FhirReference
from ldap.nhs_person import NhsPerson


def test_fhir_reference_does_not_serialise_full_value():
    practitioner = FhirPractitioner(NhsPerson({
        "uid": "123",
        "sn": "sn",
        "givenName": "givenName",
        "nhsMiddleNames": "nhsMiddleNames",
        "personalTitle": "personalTitle",
        "nhsPersonStatus": "nhsPersonStatus",
    }))
    ref = FhirReference(practitioner)

    assert ref.full_value is not None
    serialised = jsonpickle.encode(ref, unpicklable=False)
    unsearialised = jsonpickle.decode(serialised)

    assert unsearialised["reference"] == ref.reference
    assert not hasattr(unsearialised, "full_value")
