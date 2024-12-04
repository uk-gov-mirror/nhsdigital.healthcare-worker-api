def check_practitioner_entry(entry, practitioner):
    assert entry == {
        "id": practitioner.id,
        "resourceType": "Practitioner",
        "active": True,
        "identifier": [
            {"resourceType": "Identifier", "system": "https://fhir.nhs.uk/Id/sds-user-id", "value": practitioner.id}],
        "name": [{"family": practitioner.family, "given": practitioner.given, "prefix": practitioner.prefix,
                    "use": "usual", "resourceType": "Name"}]
    }


def check_practitioner_role_entry(entry, practitioner, role):
    assert entry == {
        "resourceType": "PractitionerRole",
        "id": role.role_profile_id,
        "identifier": [{
            "resourceType": "Identifier",
            "system": "https://fhir.nhs.uk/Id/sds-role-profile-id",
            "value": role.role_profile_id
        }],
        "active": True,
        "practitioner": {
            "resourceType": "Reference",
            "reference": f"Practitioner/{practitioner.id}",
            "identifier": {
                "resourceType": "Identifier",
                "system": "https://fhir.nhs.uk/Id/sds-user-id",
                "value": practitioner.id
            },
            "display": practitioner.full_name,
        },
        "organization": {
            "resourceType": "Reference",
            "reference": f"Organisation/{role.org_code}",
            "identifier": {
                "resourceType": "Identifier",
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": role.org_code
            },
            "display": role.org_name
        },
        "period": {
            "resourceType": "Period",
            "start": role.start_date,
        },
        "code": [{
            "resourceType": "CodeableConcept",
            "coding": {
                "resourceType": "Coding",
                "system": "https://fhir.nhs.uk/CodeSystem/NHSDigital-SDS-JobRoleCode",
                "code": role.role_code,
                "display": role.role_name
            }
        }]
    }
