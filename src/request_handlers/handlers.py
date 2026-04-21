import os
from typing import Dict, Type

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_bundle import FhirBundle
from fhir.fhir_bundle_entry import FhirBundleEntry
from fhir.fhir_entry_search import FhirEntrySearch
from fhir.fhir_link import FhirLink
from fhir.fhir_object import FhirObject
from hcw_exception import HcwException
from logs.log import Log
from request_handlers.base_handler import BaseHandler, HandlerResponse
from request_handlers.include_populator import get_references_to_include, get_revincludes
from request_handlers.status import StatusHandler
from request_handlers.practitioner_role import PractitionerRoleHandler
from request_handlers.practitioner import PractitionerHandler

logger = Log("handlers")


class UnknownHandlerException(HcwException):
    def __init__(self, endpoint):
        super().__init__(404, f"There is no defined handler for the provided endpoint {endpoint}", "unknown")


class RequestRouter:
    handlers: Dict[str, Type[BaseHandler]]
    supported_include_parameters: Dict[str, set[str]]

    def __init__(self):
        self.handlers = {
            "/Practitioner": PractitionerHandler,
            "/PractitionerRole": PractitionerRoleHandler,
            "/": StatusHandler,
            "/_status": StatusHandler
        }
        self.supported_include_parameters = {
            "/Practitioner": {"_revinclude"},
            "/PractitionerRole": {"_include"},
            "/": set(),
            "/_status": set(),
        }

    def handle_event(self, endpoint: str, event: APIGatewayProxyEvent) -> [FhirObject]:
        if endpoint not in self.handlers:
            raise UnknownHandlerException(endpoint)

        query_parameters = event.multi_value_query_string_parameters or {}
        self.validate_include_query_parameters(endpoint, query_parameters)

        response: HandlerResponse = self.handlers[endpoint]().get(event)

        linked = set()
        linked = linked.union(get_references_to_include(response.main_response, query_parameters))
        linked = linked.union(get_revincludes(response.main_response, query_parameters, response.related_entries))

        return self.construct_bundle(response.main_response, linked, endpoint)

    def validate_include_query_parameters(self, endpoint: str, query_parameters: dict[str, list[str] | str]) -> None:
        supported_parameters = self.supported_include_parameters.get(endpoint, set())

        for parameter_name in ["_include", "_revinclude"]:
            if parameter_name in query_parameters and parameter_name not in supported_parameters:
                raise HcwException(
                    400,
                    f"Unsupported query parameter {parameter_name} for endpoint {endpoint}",
                    "invalid",
                    "Missing or invalid query parameter(s).",
                )

    @staticmethod
    def construct_bundle(matches: [FhirObject], links: [FhirObject], path: str) -> FhirBundle:
        all_entries = set()
        for item in matches:
            search = FhirEntrySearch("match")
            all_entries.add(FhirBundleEntry(search, item))

        for item in links:
            search = FhirEntrySearch("include")
            all_entries.add(FhirBundleEntry(search, item))

        link = FhirLink("self", f"https://{os.environ["BASE_URL"]}{path}")

        return FhirBundle("searchset", len(matches), all_entries, link)
