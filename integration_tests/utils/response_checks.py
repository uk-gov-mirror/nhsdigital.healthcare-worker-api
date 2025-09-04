def check_practitioner_entry(entry, practitioner):
    if practitioner.prefix:
        expected_name = {"family": practitioner.family, "given": [practitioner.given], "prefix": [practitioner.prefix], "use": "usual"}
    else:
        expected_name = {"family": practitioner.family, "given": [practitioner.given], "use": "usual"}

    # Check individual fields instead of strict equality to allow extra identifiers
    assert entry["id"] == practitioner.id
    assert entry["resourceType"] == "Practitioner"
    assert entry["active"] == True
    assert entry["name"] == [expected_name]
    
    # Check that the required sds-user-id identifier is present (allow additional ones)
    required_identifier = {"system": "https://fhir.nhs.uk/Id/sds-user-id", "value": practitioner.id}
    assert required_identifier in entry["identifier"], f"Required identifier {required_identifier} not found in {entry['identifier']}"


def check_practitioner_role_entry(entry, practitioner, role):
    expected = {
        "resourceType": "PractitionerRole",
        "id": role.role_profile_id,
        "identifier": [{
            "system": "https://fhir.nhs.uk/Id/sds-role-profile-id",
            "value": role.role_profile_id
        }],
        "active": True,
        "practitioner": {
            "reference": f"Practitioner/{practitioner.id}",
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/sds-user-id",
                "value": practitioner.id
            },
            "display": practitioner.full_name,
        },
        "organization": {
            "reference": f"Organization/{role.org_code}",
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": role.org_code
            },
            "display": role.org_name
        },
        "period": {
            "start": role.start_date,
        },
        "code": [{
            "coding": [{
                "system": "https://fhir.nhs.uk/CodeSystem/NHSDigital-SDS-JobRoleCode",
                "code": role.role_code,
                "display": role.role_name
            }]
        }]
    }

    assert entry == expected


def check_bundle(bundle, expected_total: int):
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] == expected_total

def check_entry_wrapper(entry, search_mode: str = "match"):
    assert entry["search"] == {"mode": search_mode}
