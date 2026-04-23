import json
from pathlib import Path

import pytest

from sandbox_main import lambda_handler
from request_handlers.sandbox_static_responses import SANDBOX_SCENARIOS, get_success_example_path, success_example_is_declared_in_spec

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "specification" / "components" / "examples"
BASE_URL = "https://int.api.service.nhs.uk/healthcare-worker"
SANDBOX_UUID = "123456789012"


class LambdaContext:
    pass


def load_example(file_name: str) -> dict:
    with open(EXAMPLES_DIR / file_name, encoding="utf-8") as example_file:
        return json.load(example_file)


def load_example_path(example_path: Path) -> dict:
    with open(example_path, encoding="utf-8") as example_file:
        return json.load(example_file)


def sort_bundle_entries(bundle: dict) -> dict:
    bundle_copy = dict(bundle)
    bundle_copy["entry"] = sorted(
        bundle_copy.get("entry", []),
        key=lambda entry: (
            entry["search"]["mode"],
            entry["resource"]["resourceType"],
            entry["resource"].get("id", ""),
            entry["fullUrl"],
        ),
    )
    return bundle_copy


def sandbox_event(resource: str, query_string_parameters: dict, multi_value_query_string_parameters: dict | None = None) -> dict:
    return {
        "resource": resource,
        "queryStringParameters": query_string_parameters,
        "multiValueQueryStringParameters": multi_value_query_string_parameters or {
            key: [value] if not isinstance(value, list) else value
            for key, value in query_string_parameters.items()
        },
    }


@pytest.mark.parametrize(
    ("resource", "query_string_parameters", "example_name"),
    [
        ("/Practitioner", {"identifier": SANDBOX_UUID}, "basic"),
        (
            "/Practitioner",
            {"identifier": SANDBOX_UUID, "_revinclude": "PractitionerRole:practitioner"},
            "with-includes",
        ),
        ("/PractitionerRole", {"practitioner.identifier": SANDBOX_UUID}, "basic"),
        (
            "/PractitionerRole",
            {"practitioner.identifier": SANDBOX_UUID, "_include": "PractitionerRole:practitioner"},
            "with-includes",
        ),
    ],
)
def test_sandbox_success_scenarios_match_spec_examples(resource: str, query_string_parameters: dict, example_name: str):
    response = lambda_handler(
        sandbox_event(resource, query_string_parameters),
        LambdaContext(),
    )

    assert response["statusCode"] == 200
    assert sort_bundle_entries(json.loads(response["body"])) == sort_bundle_entries(
        load_example_path(get_success_example_path(resource, example_name))
    )


def test_sandbox_success_examples_remain_declared_in_openapi():
    for resource, config in SANDBOX_SCENARIOS.items():
        example_names = [config.default_example_name, *config.conditional_examples.values()]
        for example_name in example_names:
            assert get_success_example_path(resource, example_name).exists()
            assert success_example_is_declared_in_spec(resource, example_name)


def test_sandbox_practitioner_unknown_uuid_returns_not_found():
    response = lambda_handler(
        sandbox_event("/Practitioner", {"identifier": "999999999999"}),
        LambdaContext(),
    )

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": "error",
            "code": "unknown",
            "details": {
                "coding": [{
                    "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "404",
                    "display": "User with id 999999999999 not found",
                }]
            },
        }],
    }


def test_sandbox_practitioner_role_unknown_uuid_returns_not_found():
    response = lambda_handler(
        sandbox_event("/PractitionerRole", {"practitioner.identifier": "999999999999"}),
        LambdaContext(),
    )

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": "error",
            "code": "unknown",
            "details": {
                "coding": [{
                    "system": "https://fhir.nhs.uk/STU3/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "404",
                    "display": "User with id 999999999999 not found",
                }]
            },
        }],
    }
