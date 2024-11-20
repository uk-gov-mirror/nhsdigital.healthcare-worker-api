import json


class FhirObject:
    """
    Base Fhir Object class which all others inherit from. These are what are returned in the lambda response to
    be returned to the user.
    """
    def to_json(self):
        return json.dumps(self.__dict__)
