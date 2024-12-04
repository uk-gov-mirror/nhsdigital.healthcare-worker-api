"""
FHIR allows for _include and _revinclude query parameters which send information related to the search results.
The data layer returns these full objects, but they're not included in the normal serialisation
"""
from fhir.fhir_object import FhirObject
from fhir.fhir_reference import FhirReference, FhirReferable, FhirIdentifier
from logs.log import Log

logger = Log("include_populator")


def find_references_to_include(response: [FhirObject], resource_type: str,
                                field_reference_name: str) -> set[FhirReference]:
    matching_refs: set[FhirReference] = set()

    for entry in response:
        if entry.resourceType == resource_type and hasattr(entry, field_reference_name):
            ref: FhirReference = getattr(entry, field_reference_name)
            matching_refs.add(ref)

    return matching_refs


def find_reverse_references_to_include(response: [FhirObject], resource_type: str,
                                        field_reference_name: str, identifier: FhirIdentifier) -> set[FhirObject]:

    matches: set[FhirObject] = set()

    for entry in response:
        if entry.resourceType == resource_type and hasattr(entry, field_reference_name):
            ref: FhirReference = getattr(entry, field_reference_name)
            if ref.identifier == identifier:
                matches.add(entry)

    return matches


def add_includes_to_response(response: [FhirObject], query_parameters: [str, [str]]) -> [FhirObject]:
    includes = query_parameters.get("_include")
    if not includes:
        return response

    references_to_include: set[FhirReference] = set()

    for include in includes:
        resource_type, field_reference_name, *_ = include.split(":")
        references_to_include = references_to_include.union(find_references_to_include(response, resource_type, field_reference_name))

    response.extend(map(lambda x: x.full_value, references_to_include))
    return response


def add_revincludes_to_response(response: [FhirObject], query_parameters: [str, [str]],
                                related_entries: list[FhirObject]) -> [FhirObject]:
    includes = query_parameters.get("_revinclude")
    if not includes:
        return response

    resources_to_include: set[FhirObject] = set()

    for entry in response:
        if isinstance(entry, FhirReferable):
            for include in includes:
                resource_type, field_reference_name, *_ = include.split(":")
                matches = find_reverse_references_to_include(related_entries, resource_type,
                                                                field_reference_name, entry.get_identifier())

                resources_to_include = resources_to_include.union(matches)

    response.extend(resources_to_include)
    return response
