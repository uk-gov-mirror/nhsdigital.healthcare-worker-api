import json
from pathlib import Path

from sandbox_main import lambda_handler

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "specification" / "components" / "examples"
BASE_URL = "https://int.api.service.nhs.uk/healthcare-worker"
SANDBOX_UUID = "123456789012"


class LambdaContext:
    pass


def load_example(file_name: str) -> dict:
    with open(EXAMPLES_DIR / file_name, encoding="utf-8") as example_file:
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


def test_sandbox_practitioner_basic_matches_spec_example():
    response = lambda_handler(
        sandbox_event("/Practitioner", {"identifier": SANDBOX_UUID}),
        LambdaContext(),
    )

    assert response["statusCode"] == 200
    assert sort_bundle_entries(json.loads(response["body"])) == sort_bundle_entries(
        load_example("GetHealthcareWorkerDetailsResponseSuccessBasic.json")
    )


def test_sandbox_practitioner_with_revinclude_matches_spec_example():
    response = lambda_handler(
        sandbox_event(
            "/Practitioner",
            {"identifier": SANDBOX_UUID, "_revinclude": "PractitionerRole:practitioner"},
        ),
        LambdaContext(),
    )

    assert response["statusCode"] == 200
    assert sort_bundle_entries(json.loads(response["body"])) == sort_bundle_entries(
        load_example("GetHealthcareWorkerDetailsResponseSuccessWithIncludes.json")
    )


def test_sandbox_practitioner_role_basic_matches_spec_example():
    response = lambda_handler(
        sandbox_event("/PractitionerRole", {"practitioner.identifier": SANDBOX_UUID}),
        LambdaContext(),
    )

    assert response["statusCode"] == 200
    assert sort_bundle_entries(json.loads(response["body"])) == sort_bundle_entries(
        load_example("GetHealthcareWorkerRoleDetailsResponseSuccessBasic.json")
    )


def test_sandbox_practitioner_role_with_include_matches_spec_example():
    response = lambda_handler(
        sandbox_event(
            "/PractitionerRole",
            {"practitioner.identifier": SANDBOX_UUID, "_include": "PractitionerRole:practitioner"},
        ),
        LambdaContext(),
    )

    assert response["statusCode"] == 200
    assert sort_bundle_entries(json.loads(response["body"])) == sort_bundle_entries(
        load_example("GetHealthcareWorkerRoleDetailsResponseSuccessWithIncludes.json")
    )


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
