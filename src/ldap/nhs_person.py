def from_list(values: [str]) -> str:
    if not values or len(values) == 0:
        return ""

    return values[0]


class NhsPerson(object):
    uid: str
    sn: str
    given_name: str
    nhs_middle_names: str
    personal_title: str
    nhs_person_status: str

    def __init__(self, uid: [str], sn: [str], given_name: [str], nhs_middle_names: [str], personal_title: [str],
                    nhs_person_status: str) -> None:
        self.uid = from_list(uid)
        self.sn = from_list(sn)
        self.given_name = from_list(given_name)
        self.nhs_middle_names = " ".join(nhs_middle_names or [])
        self.personal_title = from_list(personal_title)
        self.nhs_person_status = nhs_person_status
