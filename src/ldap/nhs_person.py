from datetime import date, datetime
from typing import Optional

from logs.log import Log

logger = Log("nhs_person")


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
    joined: Optional[date] = None
    ods_code: str
    org_name: str
    nhs_id_code: str

    def __init__(self, org_person_attrs: dict[str, str]) -> None:
        self.org_person_id = from_list_or_string(org_person_attrs["uniqueIdentifier"])

        # Safe parsing for nhsOrgOpenDate
        open_date_str = from_list_or_string(org_person_attrs.get("nhsOrgOpenDate", ""))
        if open_date_str and open_date_str.strip():
            try:
                self.joined = datetime.strptime(open_date_str, "%Y%m%d").date()
            except ValueError as e:
                logger.warning(f"Invalid nhsOrgOpenDate format for org person: '{open_date_str}' - {e}", "INVALID_ORG_OPEN_DATE", org_person_attrs.get("uniqueIdentifier", "unknown"))

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
    speciality: str
    rpsgb_number: str
    gmc_number: str
    gdp_number: str
    gdc_number: str
    rcn_number: str
    nmc_number: str
    gmp_number: str
    consultant_code: str
    nacs_practitioner_code: str

    def __init__(self, person_attrs: dict[str, str]) -> None:
        self.uid = from_list_or_string(person_attrs.get("uid", None))
        self.sn = from_list_or_string(person_attrs.get("sn", None))
        self.given_name = from_list_or_string(person_attrs.get("givenName", None))
        self.nhs_middle_names = from_list_or_string(person_attrs.get("nhsMiddleNames", None))
        self.personal_title = from_list_or_string(person_attrs.get("personalTitle", None))
        self.nhs_person_status = from_list_or_string(person_attrs.get("nhsPersonStatus", None))
        self.speciality = from_list_or_string(person_attrs.get("nhsPrinOcc", None))
        self.rpsgb_number = from_list_or_string(person_attrs.get("nhsRPSGB", None))
        self.gmc_number = from_list_or_string(person_attrs.get("nhsGMC", None))
        self.gdp_number = from_list_or_string(person_attrs.get("nhsGDP", None))
        self.gdc_number = from_list_or_string(person_attrs.get("nhsGDC", None))
        self.rcn_number = from_list_or_string(person_attrs.get("nhsRCN", None))
        self.nmc_number = from_list_or_string(person_attrs.get("nhsNMC", None))
        self.gmp_number = from_list_or_string(person_attrs.get("nhsGMP", None))
        self.consultant_code = from_list_or_string(person_attrs.get("nhsConsultant", None))
        self.nacs_practitioner_code = from_list_or_string(person_attrs.get("nhsOcsPrCode", None))


class NhsOrgPersonRole:
    profile_id: str
    business_function_codes: list[str]
    job_role: str
    job_role_code: str
    role_granted: Optional[date] = None
    role_stopped: Optional[date] = None
    nacs_site_names: [str]
    nacs_site_codes: [str]
    practitioner: Optional[NhsPerson]
    org_person: Optional[NhsOrgPerson]

    def __init__(self, role_attrs: dict) -> None:
        self.profile_id = from_list_or_string(role_attrs.get("uniqueIdentifier", []))
        self.business_function_codes = role_attrs.get("nhsBusinessFunctionsCodes", [])
        self.business_functions = role_attrs.get("nhsBusinessFunctions", None)
        self.job_role = from_list_or_string(role_attrs.get("nhsJobRole", []))
        self.job_role_code = from_list_or_string(role_attrs.get("nhsJobRoleCode", []))
        self.nhs_id_code = from_list_or_string(role_attrs.get("nhsIDCode", []))
        self.nacs_site_names = role_attrs.get("nhsSiteNames", None)
        self.nacs_site_codes = role_attrs.get("nhsSiteCodes", None)

        open_date_str = from_list_or_string(role_attrs.get("nhsOrgOpenDate", ""))
        if open_date_str and open_date_str.strip():
            try:
                self.role_granted = datetime.strptime(open_date_str, "%Y%m%d").date()
            except ValueError as e:
                logger.warning(f"Invalid nhsOrgOpenDate format: '{open_date_str}' - {e}", "INVALID_OPEN_DATE", role_attrs.get("uniqueIdentifier", "unknown"))

        if role_attrs.get("nhsOrgCloseDate"):
            close_date_str = from_list_or_string(role_attrs["nhsOrgCloseDate"])
            if close_date_str and close_date_str.strip():
                try:
                    self.role_stopped = datetime.strptime(close_date_str, "%Y%m%d").date()
                except ValueError as e:
                    logger.warning(f"Invalid nhsOrgCloseDate format: '{close_date_str}' - {e}", "INVALID_CLOSE_DATE", role_attrs.get("uniqueIdentifier", "unknown"))
