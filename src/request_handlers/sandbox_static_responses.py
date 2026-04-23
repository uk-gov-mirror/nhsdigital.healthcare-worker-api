import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

SANDBOX_UUID = "123456789012"
SPECIFICATION_FILE = Path("specification") / "healthcare-worker-api.yaml"
EXAMPLES_SUBPATH = Path("specification") / "components" / "examples"
SUCCESS_EXAMPLE_REFERENCES: dict[tuple[str, str], Path] = {
    ("/Practitioner", "basic"): EXAMPLES_SUBPATH / "GetHealthcareWorkerDetailsResponseSuccessBasic.json",
    ("/Practitioner", "with-includes"): EXAMPLES_SUBPATH / "GetHealthcareWorkerDetailsResponseSuccessWithIncludes.json",
    ("/PractitionerRole", "basic"): EXAMPLES_SUBPATH / "GetHealthcareWorkerRoleDetailsResponseSuccessBasic.json",
    ("/PractitionerRole", "with-includes"): EXAMPLES_SUBPATH / "GetHealthcareWorkerRoleDetailsResponseSuccessWithIncludes.json",
}


@dataclass(frozen=True)
class SandboxEndpointConfig:
    identifier_parameter: str
    include_parameter: str | None
    default_example_name: str
    conditional_examples: dict[str, str]

    def get_example_name(self, query_parameters: dict[str, str]) -> str:
        if not self.include_parameter:
            return self.default_example_name

        include_value = query_parameters.get(self.include_parameter)
        return self.conditional_examples.get(include_value, self.default_example_name)


SANDBOX_SCENARIOS: dict[str, SandboxEndpointConfig] = {
    "/Practitioner": SandboxEndpointConfig(
        identifier_parameter="identifier",
        include_parameter="_revinclude",
        default_example_name="basic",
        conditional_examples={"PractitionerRole:practitioner": "with-includes"},
    ),
    "/PractitionerRole": SandboxEndpointConfig(
        identifier_parameter="practitioner.identifier",
        include_parameter="_include",
        default_example_name="basic",
        conditional_examples={"PractitionerRole:practitioner": "with-includes"},
    ),
}


def get_sandbox_response(event: APIGatewayProxyEvent) -> tuple[int, str] | None:
    config = SANDBOX_SCENARIOS.get(event.resource)
    if not config:
        return None

    query_parameters = event.query_string_parameters or {}
    practitioner_id = query_parameters.get(config.identifier_parameter)
    if practitioner_id != SANDBOX_UUID:
        return _not_found_response(practitioner_id)

    example_name = config.get_example_name(query_parameters)
    return 200, _load_success_example(event.resource, example_name)


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


def get_success_example_path(endpoint: str, example_name: str) -> Path:
    try:
        relative_path = _get_success_example_references()[(endpoint, example_name)]
    except KeyError as exc:
        raise KeyError(f"Sandbox example {example_name!r} for endpoint {endpoint!r} is not configured") from exc

    return _get_repository_root() / relative_path


def success_example_is_declared_in_spec(endpoint: str, example_name: str) -> bool:
    example_path = _get_success_example_references()[(endpoint, example_name)]
    external_value = example_path.relative_to("specification").as_posix()
    return f"externalValue: '{external_value}'" in _get_specification_text()


def _load_success_example(endpoint: str, example_name: str) -> str:
    with open(get_success_example_path(endpoint, example_name), encoding="utf-8") as example_file:
        return example_file.read()


@lru_cache(maxsize=1)
def _get_success_example_references() -> dict[tuple[str, str], Path]:
    return SUCCESS_EXAMPLE_REFERENCES


@lru_cache(maxsize=1)
def _get_specification_text() -> str:
    with open(_get_repository_root() / SPECIFICATION_FILE, encoding="utf-8") as spec_file:
        return spec_file.read()


@lru_cache(maxsize=1)
def _get_repository_root() -> Path:
    current_file = Path(__file__).resolve()
    candidate_roots = [current_file.parents[2], current_file.parents[1]]

    for root in candidate_roots:
        if (root / SPECIFICATION_FILE).exists() and (root / EXAMPLES_SUBPATH).exists():
            return root

    raise FileNotFoundError(f"Could not locate sandbox specification under {SPECIFICATION_FILE}")
