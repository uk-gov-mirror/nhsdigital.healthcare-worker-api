import jsonpickle

from fhir.fhir_worker import FhirWorker, FhirIdentifier, FhirName


# JSON serialisation is key to how this information is returned, and we are relying on a pip dependency to serialise
# the structure with embedded lists. In the future if this is time-consuming to maintain and we have proven faith
# in the jsonpickle package, then we might want to remove this test.
def test_fhir_worker_serialisation():
    worker = FhirWorker()
    worker.id = "uid"
    worker.resourceType = "resourceType"
    worker.active = True
    worker.identifier = [FhirIdentifier("system", "value")]
    worker.name = [FhirName("usual", "Family", "Given Middle", "Mr")]

    serialised = jsonpickle.encode(worker, unpicklable=False)

    assert serialised == ('{"id": "uid", "resourceType": "resourceType", "active": true, "identifier": '
                            '[{"system": "system", "value": "value"}], "name": [{"use": "usual", "family": "Family", '
                            '"given": "Given Middle", "prefix": "Mr"}]}')

