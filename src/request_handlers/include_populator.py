"""
FHIR allows for _include and _revinclude query parameters which send information related to the search results.
The data layer returns these full objects, but they're not included in the normal serialisation
"""
from fhir.fhir_object import FhirObject
from fhir.fhir_reference import FhirReference, FhirReferable, FhirIdentifier
from hcw_exception import HcwException
from logs.log import Log

logger = Log("include_populator")


def get_query_parameter_values(query_parameters: dict[str, list[str] | str], parameter_name: str) -> list[str]:
    values = query_parameters.get(parameter_name)
    if not values:
        return []

    if isinstance(values, str):
        return [values]

    return values


def parse_include_value(include: str, parameter_name: str) -> tuple[str, str]:
    include_parts = include.split(":")
    if len(include_parts) < 2 or not include_parts[0] or not include_parts[1]:
        raise HcwException(
            400,
            f"Invalid value '{include}' for query parameter {parameter_name}",
            "invalid",
            "Missing or invalid query parameter(s).",
        )

    return include_parts[0], include_parts[1]


def find_referenced_values(response: [FhirObject], resource_type: str,
                                field_reference_name: str) -> set[FhirObject]:
    matching_refs: set[FhirReference] = set()

    for entry in response:
        if entry.resourceType == resource_type and hasattr(entry, field_reference_name):
            ref: FhirReference = getattr(entry, field_reference_name)
            matching_refs.add(ref.full_value)

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


def get_references_to_include(response: [FhirObject], query_parameters: [str, [str]]) -> [FhirObject]:
    includes = get_query_parameter_values(query_parameters, "_include")
    if not includes:
        return []

    references_to_include: set[FhirObject] = set()
    for include in includes:
        resource_type, field_reference_name = parse_include_value(include, "_include")
        references_to_include = references_to_include.union(find_referenced_values(response, resource_type, field_reference_name))

    return references_to_include


def get_revincludes(response: [FhirObject], query_parameters: [str, [str]],
                                related_entries: list[FhirObject]) -> [FhirObject]:
    includes = get_query_parameter_values(query_parameters, "_revinclude")
    logger.info(f"Revincludes = {includes}","REQ_REVINCLUDES", "null")
    if not includes:
        return []

    resources_to_include: set[FhirObject] = set()
    for entry in response:
        if isinstance(entry, FhirReferable):
            logger.info(f"Checking for includes on {entry}", "REQ_REVINCLUDES_CHECK", "null")
            for include in includes:
                resource_type, field_reference_name = parse_include_value(include, "_revinclude")
                matches = find_reverse_references_to_include(related_entries, resource_type,
                                                                field_reference_name, entry.get_identifier())

                resources_to_include = resources_to_include.union(matches)
                logger.info("Added revinclude","REQ_REVINCLUDES_ADDED", "null")

    return resources_to_include
