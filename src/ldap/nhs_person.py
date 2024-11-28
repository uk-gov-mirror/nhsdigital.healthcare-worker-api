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


class NhsPerson(object):
    uid: str
    sn: str
    given_name: str
    nhs_middle_names: str
    personal_title: str
    nhs_person_status: str

    def __init__(self, uid: [str], sn: [str], given_name: [str], nhs_middle_names: [str], personal_title: [str],
                    nhs_person_status: str) -> None:
        self.uid = from_list_or_string(uid)
        self.sn = from_list_or_string(sn)
        self.given_name = from_list_or_string(given_name)
        self.nhs_middle_names = from_list_or_string(nhs_middle_names)
        self.personal_title = from_list_or_string(personal_title)
        self.nhs_person_status = from_list_or_string(nhs_person_status)
