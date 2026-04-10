KNOWN_USER = "152133081108"
NO_PREFIX_OR_MIDDLE_NAME = "152133095108"
MULTIPLE_MIDDLE_NAMES = "152133102102"

SINGLE_ROLE = NO_PREFIX_OR_MIDDLE_NAME
NO_ROLE = MULTIPLE_MIDDLE_NAMES

# HCW-183 Missing date test scenarios
MISSING_ORG_PERSON_DATES = "102013428983"             # nhsOrgPerson: no open, no close → should be included
MISSING_ORG_PERSON_OPEN_PAST_CLOSE = "927501956548"   # nhsOrgPerson: no open, past close → should be included
MISSING_ROLE_OPEN_DATE_PAST_CLOSE = "100121123891"    # nhsOrgPersonRole: no open, past close → should be filtered out
MISSING_ROLE_DATES = "150279799109"                   # nhsOrgPersonRole: no open, no close → should be included


class RoleExample:
    role_profile_id: str
    org_code: str
    org_name: str
    start_date: str
    role_code: str
    role_name: str

    def __init__(self, role_profile_id: str, org_code: str, org_name: str, start_date: str, role_code: str,
                    role_name: str):
        self.role_profile_id = role_profile_id
        self.org_code = org_code
        self.org_name = org_name
        self.start_date = start_date
        self.role_code = role_code
        self.role_name = role_name


class PractitionerExample:
    id: str
    prefix: str
    given: str
    family: str
    full_name: str
    roles: list[RoleExample]

    def __init__(self, identifier: str, prefix: str, given: str, family: str, full_name: str,
                    roles: list[RoleExample]) -> None:
        self.id = identifier
        self.prefix = prefix
        self.given = given
        self.family = family
        self.full_name = full_name
        self.roles = roles


practitioners: [PractitionerExample] = [
    PractitionerExample(KNOWN_USER, "Mr", "Jack AutoTestM", "Joe", "Mr Jack AutoTestM Joe", []),
    PractitionerExample(NO_PREFIX_OR_MIDDLE_NAME, "", "Finnley", "Reeve", "Finnley Reeve",
                        [RoleExample("152133101104", "CIM1",
                                        "CIM ONE", "2026-03-25",
                                        "S8001:G8005:R8015",
                                        "\"Support\":\"Systems Support\":\"Systems Support Access Role\"")]),
    PractitionerExample(MULTIPLE_MIDDLE_NAMES, "Miss", "Shayla Cailin Seanna Cayley", "Ashworth",
                        "Miss Shayla Cailin Seanna Cayley Ashworth", []),
    PractitionerExample(MISSING_ORG_PERSON_DATES, "Dr", "LOUISE", "STEENE", "Dr LOUISE STEENE", []),
    PractitionerExample(MISSING_ORG_PERSON_OPEN_PAST_CLOSE, "Mr", "KARTHIK J", "BVM", "Mr KARTHIK J BVM", []),
    PractitionerExample(MISSING_ROLE_OPEN_DATE_PAST_CLOSE, "Mr", "Elvis", "Presley", "Mr Elvis Presley",
                        [RoleExample("100006095908", "Y51",
                                        "", "",
                                        "S0080:G0440:R5000",
                                        "\"Admin & Clerical\":\"Admin\":\"Sponsor\"")]),
    PractitionerExample(MISSING_ROLE_DATES, "Dr", "Shikha", "Tiwari", "Dr Shikha Tiwari",
                        [RoleExample("150452057105", "Y51",
                                        "", "",
                                        "S0070:G0380:R0002",
                                        "\"Add\'l Clinical Services\":\"Non Clinical - Add Clin Serv\":\"Porter\"")]),
]


def get_practitioners_example(practitioner_id: str) -> PractitionerExample:
    return next(filter(lambda p: p.id == practitioner_id, practitioners))
