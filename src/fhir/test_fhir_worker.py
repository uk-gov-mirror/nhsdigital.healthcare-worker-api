import json

import jsonpickle

from fhir.worker import FhirWorker, FhirIdentifier, FhirName


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

