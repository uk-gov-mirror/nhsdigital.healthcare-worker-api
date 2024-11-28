KNOWN_USER = "150549950108"
NO_PREFIX_OR_MIDDLE_NAME = "151504269102"
MULTIPLE_MIDDLE_NAMES = "151504270100"


class PractitionerExample:
    id: str
    prefix: str
    given: str
    family: str

    def __init__(self, identifier: str, prefix: str, given: str, family: str):
        self.id = identifier
        self.prefix = prefix
        self.given = given
        self.family = family


practitioners: [PractitionerExample] = [
    PractitionerExample(KNOWN_USER, "Mr", "Jitendra", "Banshpal"),
    PractitionerExample(NO_PREFIX_OR_MIDDLE_NAME, "", "Finnley", "Reeve"),
    PractitionerExample(MULTIPLE_MIDDLE_NAMES, "Miss", "Shayla Cailin Seanna Cayley", "Ashworth")
]


def get_practitioners_example(practitioner_id: str) -> PractitionerExample:
    return next(filter(lambda p: p.id == practitioner_id, practitioners))

