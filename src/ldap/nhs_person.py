from datetime import date, datetime
from typing import Optional


def from_list_or_string(value) -> str:
    # I've seen at least middle name have both an empty array and a string value, we're only expecting to ever
    # have a single value for all these fields so if it's an array take the first value and if it's a string
    # just pass it through
    # Input value is either a str or an array of str
    if isinstance(value, str):
        return value

    if not value or len(value) == 0:
        return ""

    return value[0]


class NhsOrgPerson:
    org_person_id: str
    joined: date
    ods_code: str
    org_name: str
    nhs_id_code: str

    def __init__(self, org_person_attrs: dict[str, str]) -> None:
        self.org_person_id = from_list_or_string(org_person_attrs["uniqueIdentifier"])
        self.joined = datetime.strptime(from_list_or_string(org_person_attrs["nhsOpenDate"]), "%Y%m%d").date()
        self.ods_code = from_list_or_string(org_person_attrs["nhsIDCode"])
        self.org_name = from_list_or_string(org_person_attrs["o"])
        self.nhs_id_code = from_list_or_string(org_person_attrs["nhsIDCode"])


class NhsPerson:
    uid: str
    sn: str
    given_name: str
    nhs_middle_names: str
    personal_title: str
    nhs_person_status: str

    def __init__(self, person_attrs: dict[str, str]) -> None:
        self.uid = from_list_or_string(person_attrs["uid"])
        self.sn = from_list_or_string(person_attrs["sn"])
        self.given_name = from_list_or_string(person_attrs["givenName"])
        self.nhs_middle_names = from_list_or_string(person_attrs["nhsMiddleNames"])
        self.personal_title = from_list_or_string(person_attrs["personalTitle"])
        self.nhs_person_status = from_list_or_string(person_attrs["nhsPersonStatus"])


class NhsOrgPersonRole:
    profile_id: str
    business_function_codes: list[str]
    job_role: str
    job_role_code: str
    role_granted: date
    role_stopped: Optional[date] = None
    practitioner: Optional[NhsPerson]
    org_person: Optional[NhsOrgPerson]

    def __init__(self, role_attrs: dict) -> None:
        self.profile_id = from_list_or_string(role_attrs["uniqueIdentifier"])
        self.business_function_codes = role_attrs["nhsBusinessFunctionsCodes"]
        self.business_functions = role_attrs["nhsBusinessFunctions"]
        self.job_role = from_list_or_string(role_attrs["nhsJobRole"])
        self.job_role_code = from_list_or_string(role_attrs["nhsJobRoleCode"])
        self.nhs_id_code = from_list_or_string(role_attrs["nhsIDCode"])

        self.role_granted = datetime.strptime(from_list_or_string(role_attrs["nhsOpenDate"]), "%Y%m%d").date()
        if role_attrs["nhsCloseDate"]:
            self.role_stopped = datetime.strptime(from_list_or_string(role_attrs["nhsCloseDate"]), "%Y%m%d").date()
