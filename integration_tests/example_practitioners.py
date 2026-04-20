from .config.current_env import get_current_env
from .config.ft_environment import FtEnvironmentConfig
from .config.int import IntEnvironmentConfig

_ENV_TEST_DATA = {
    "int": {
        "KNOWN_USER": "555390115106",
        "NO_PREFIX_OR_MIDDLE_NAME": "555390121104",
        "MULTIPLE_MIDDLE_NAMES": "555390124108",
        "SINGLE_ROLE": "555390121104",
        "NO_ROLE": "555390124108",
        "MISSING_ORG_PERSON_DATES": "555390125105",
        "MISSING_ORG_PERSON_OPEN_PAST_CLOSE": "555390126103",
        "MISSING_ROLE_OPEN_DATE_PAST_CLOSE": "555390127101",
        "MISSING_ROLE_DATES": "555390130105",
        "ROLE_SINGLE": "555390101104",
        "ROLE_MISSING_OPEN_DATE_PAST_CLOSE": "555390095908",
        "ROLE_MISSING_DATES": "555390057105",
        "practitioners": {
            "KNOWN_USER": {"prefix": "Miss", "given": "Lydia", "family": "Joe", "full_name": "Miss Lydia Jael Joe", "roles": []},
            "NO_PREFIX_OR_MIDDLE_NAME": {"prefix": "", "given": "Solomon", "family": "John", "full_name": "Solomon John", "roles": [
                {"role_profile_id": "ROLE_SINGLE", "org_code": "INT1", "org_name": "INT TEST ORG", "start_date": "2024-01-01",
                 "role_code": "S0010:G0010:R0010", "role_name": "\"Test\":\"Test\":\"Test Role\""}
            ]},
            "MULTIPLE_MIDDLE_NAMES": {"prefix": "Ms", "given": "Mary Jane", "family": "Doe", "full_name": "Ms Mary Jane Doe", "roles": []},
            "MISSING_ORG_PERSON_DATES": {"prefix": "Dr", "given": "John", "family": "Missing", "full_name": "Dr John Missing", "roles": []},
            "MISSING_ORG_PERSON_OPEN_PAST_CLOSE": {"prefix": "Mr", "given": "Past", "family": "Close", "full_name": "Mr Past Close", "roles": []},
            "MISSING_ROLE_OPEN_DATE_PAST_CLOSE": {"prefix": "Mrs", "given": "Role", "family": "Missing", "full_name": "Mrs Role Missing", "roles": [
                {"role_profile_id": "ROLE_MISSING_OPEN_DATE_PAST_CLOSE", "org_code": "INT1", "org_name": "", "start_date": "",
                 "role_code": "S0020:G0020:R0020", "role_name": "\"Admin\":\"Test\":\"Test Admin\""}
            ]},
            "MISSING_ROLE_DATES": {"prefix": "Dr", "given": "Date", "family": "Missing", "full_name": "Dr Date Missing", "roles": [
                {"role_profile_id": "ROLE_MISSING_DATES", "org_code": "INT1", "org_name": "", "start_date": "",
                 "role_code": "S0030:G0030:R0030", "role_name": "\"Clinical\":\"Test\":\"Test Clinical\""}
            ]},
        }
    },
    "ft": {
        "KNOWN_USER": "150549950108",
        "NO_PREFIX_OR_MIDDLE_NAME": "151504269102",
        "MULTIPLE_MIDDLE_NAMES": "151504270100",
        "SINGLE_ROLE": "151504269102",
        "NO_ROLE": "151504270100",
        "MISSING_ORG_PERSON_DATES": "102013428983",
        "MISSING_ORG_PERSON_OPEN_PAST_CLOSE": "927501956548",
        "MISSING_ROLE_OPEN_DATE_PAST_CLOSE": "100121123891",
        "MISSING_ROLE_DATES": "150279799109",
        "ROLE_SINGLE": "151504442105",
        "ROLE_MISSING_OPEN_DATE_PAST_CLOSE": "100006095908",
        "ROLE_MISSING_DATES": "150452057105",
        "practitioners": {
            "KNOWN_USER": {"prefix": "Mr", "given": "Jitendra", "family": "Banshpal", "full_name": "Mr Jitendra Banshpal", "roles": []},
            "NO_PREFIX_OR_MIDDLE_NAME": {"prefix": "", "given": "Finnley", "family": "Reeve", "full_name": "Finnley Reeve", "roles": [
                {"role_profile_id": "ROLE_SINGLE", "org_code": "Y51", "org_name": "THE NORTH MIDLANDS AND EAST PROGRAMME FOR IT (NMEPFIT)", "start_date": "2024-11-27",
                 "role_code": "S0070:G0380:R0002", "role_name": "\"Add'l Clinical Services\":\"Non Clinical - Add Clin Serv\":\"Porter\""}
            ]},
            "MULTIPLE_MIDDLE_NAMES": {"prefix": "Miss", "given": "Shayla Cailin Seanna Cayley", "family": "Ashworth", "full_name": "Miss Shayla Cailin Seanna Cayley Ashworth", "roles": []},
            "MISSING_ORG_PERSON_DATES": {"prefix": "Dr", "given": "LOUISE", "family": "STEENE", "full_name": "Dr LOUISE STEENE", "roles": []},
            "MISSING_ORG_PERSON_OPEN_PAST_CLOSE": {"prefix": "Mr", "given": "KARTHIK J", "family": "BVM", "full_name": "Mr KARTHIK J BVM", "roles": []},
            "MISSING_ROLE_OPEN_DATE_PAST_CLOSE": {"prefix": "Mr", "given": "Elvis", "family": "Presley", "full_name": "Mr Elvis Presley", "roles": [
                {"role_profile_id": "ROLE_MISSING_OPEN_DATE_PAST_CLOSE", "org_code": "Y51", "org_name": "", "start_date": "",
                 "role_code": "S0080:G0440:R5000", "role_name": "\"Admin & Clerical\":\"Admin\":\"Sponsor\""}
            ]},
            "MISSING_ROLE_DATES": {"prefix": "Dr", "given": "Shikha", "family": "Tiwari", "full_name": "Dr Shikha Tiwari", "roles": [
                {"role_profile_id": "ROLE_MISSING_DATES", "org_code": "Y51", "org_name": "", "start_date": "",
                 "role_code": "S0070:G0380:R0002", "role_name": "\"Add\'l Clinical Services\":\"Non Clinical - Add Clin Serv\":\"Porter\""}
            ]},
        }
    },
}


def _get_test_environment() -> str:
    try:
        env = get_current_env()
    except Exception:
        return "int"

    if isinstance(env, FtEnvironmentConfig):
        return "ft"
    if isinstance(env, IntEnvironmentConfig):
        return "int"

    env_name = env.__class__.__name__.lower()
    if env_name.startswith("ft"):
        return "ft"
    if env_name.startswith("int"):
        return "int"

    raise NotImplementedError("Unsupported test environment for practitioner examples")


def _get_env_data(name: str) -> str:
    env = _get_test_environment()
    return _ENV_TEST_DATA[env][name]


KNOWN_USER = _get_env_data("KNOWN_USER")
NO_PREFIX_OR_MIDDLE_NAME = _get_env_data("NO_PREFIX_OR_MIDDLE_NAME")
MULTIPLE_MIDDLE_NAMES = _get_env_data("MULTIPLE_MIDDLE_NAMES")

SINGLE_ROLE = _get_env_data("SINGLE_ROLE")
NO_ROLE = _get_env_data("NO_ROLE")

# HCW-183 Missing date test scenarios
MISSING_ORG_PERSON_DATES = _get_env_data("MISSING_ORG_PERSON_DATES")             # nhsOrgPerson: no open, no close → should be included
MISSING_ORG_PERSON_OPEN_PAST_CLOSE = _get_env_data("MISSING_ORG_PERSON_OPEN_PAST_CLOSE")   # nhsOrgPerson: no open, past close → should be included
MISSING_ROLE_OPEN_DATE_PAST_CLOSE = _get_env_data("MISSING_ROLE_OPEN_DATE_PAST_CLOSE")    # nhsOrgPersonRole: no open, past close → should be filtered out
MISSING_ROLE_DATES = _get_env_data("MISSING_ROLE_DATES")                   # nhsOrgPersonRole: no open, no close → should be included


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

def _build_practitioners() -> list[PractitionerExample]:
    env = _get_test_environment()
    env_data = _ENV_TEST_DATA[env]
    practitioners_data = env_data["practitioners"]

    practitioners_list = []
    for practitioner_key, practitioner_details in practitioners_data.items():
        practitioner_id = env_data[practitioner_key]
        roles = []
        for role_data in practitioner_details["roles"]:
            role_profile_id = env_data[role_data["role_profile_id"]]
            role = RoleExample(
                role_profile_id=role_profile_id,
                org_code=role_data["org_code"],
                org_name=role_data["org_name"],
                start_date=role_data["start_date"],
                role_code=role_data["role_code"],
                role_name=role_data["role_name"]
            )
            roles.append(role)

        practitioner = PractitionerExample(
            identifier=practitioner_id,
            prefix=practitioner_details["prefix"],
            given=practitioner_details["given"],
            family=practitioner_details["family"],
            full_name=practitioner_details["full_name"],
            roles=roles
        )
        practitioners_list.append(practitioner)

    return practitioners_list

practitioners: list[PractitionerExample] = _build_practitioners()


def get_practitioners_example(practitioner_id: str) -> PractitionerExample:
    return next(filter(lambda p: p.id == practitioner_id, practitioners))
