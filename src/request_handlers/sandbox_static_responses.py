import json
from pathlib import Path

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

SANDBOX_UUID = "123456789012"
EXAMPLES_SUBPATH = Path("specification") / "components" / "examples"


def get_sandbox_response(event: APIGatewayProxyEvent) -> tuple[int, str] | None:
    query_parameters = event.query_string_parameters or {}

    if event.resource == "/Practitioner":
        return _get_practitioner_response(query_parameters)

    if event.resource == "/PractitionerRole":
        return _get_practitioner_role_response(query_parameters)

    return None


def _get_practitioner_response(query_parameters: dict[str, str]) -> tuple[int, str]:
    practitioner_id = query_parameters.get("identifier")
    if practitioner_id != SANDBOX_UUID:
        return _not_found_response(practitioner_id)

    if query_parameters.get("_revinclude") == "PractitionerRole:practitioner":
        return 200, _load_example("GetHealthcareWorkerDetailsResponseSuccessWithIncludes.json")

    return 200, _load_example("GetHealthcareWorkerDetailsResponseSuccessBasic.json")


def _get_practitioner_role_response(query_parameters: dict[str, str]) -> tuple[int, str]:
    practitioner_id = query_parameters.get("practitioner.identifier")
    if practitioner_id != SANDBOX_UUID:
        return _not_found_response(practitioner_id)

    if query_parameters.get("_include") == "PractitionerRole:practitioner":
        return 200, _load_example("GetHealthcareWorkerRoleDetailsResponseSuccessWithIncludes.json")

    return 200, _load_example("GetHealthcareWorkerRoleDetailsResponseSuccessBasic.json")


def _not_found_response(practitioner_id: str | None) -> tuple[int, str]:
    response = {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": "error",
            "code": "unknown",
            "details": {
                "coding": [{
                    "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "404",
                    "display": f"User with id {practitioner_id} not found",
                }]
            },
        }],
    }

    return 404, json.dumps(response)


def _load_example(file_name: str) -> str:
    with open(_get_examples_directory() / file_name, encoding="utf-8") as example_file:
        return example_file.read()


def _get_examples_directory() -> Path:
    current_file = Path(__file__).resolve()
    candidate_roots = [current_file.parents[2], current_file.parents[1]]

    for root in candidate_roots:
        examples_directory = root / EXAMPLES_SUBPATH
        if examples_directory.exists():
            return examples_directory

    raise FileNotFoundError(f"Could not locate sandbox example files under {EXAMPLES_SUBPATH}")