from typing import Dict, Type

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_object import FhirObject
from fhir.fhir_practitioner import FhirPractitioner
from hcw_exception import HcwException
from logs.log import Log
from request_handlers.base_handler import BaseHandler
from request_handlers.include_populator import add_includes_to_response, add_revincludes_to_response
from request_handlers.status import StatusHandler
from request_handlers.practitioner_role import PractitionerRole
from request_handlers.practitioner import PractitionerHandler

logger = Log("handlers")


class UnknownHandlerException(HcwException):
    def __init__(self, endpoint):
        super().__init__(404, f"There is no defined handler for the provided endpoint {endpoint}")


class RequestRouter:
    handlers: Dict[str, Type[BaseHandler]]

    def __init__(self):
        self.handlers = {
            "/Practitioner": PractitionerHandler,
            "/PractitionerRole": PractitionerRole,
            "/": StatusHandler,
            "/_status": StatusHandler
        }

    def handle_event(self, endpoint: str, event: APIGatewayProxyEvent) -> [FhirObject]:
        if endpoint not in self.handlers:
            raise UnknownHandlerException(endpoint)

        response = self.handlers[endpoint]().get(event)
        logger.info(f"Got response from handler of {response.main_response}")

        response_with_includes = add_includes_to_response(response.main_response, event.multi_value_query_string_parameters)
        return add_revincludes_to_response(response_with_includes, event.multi_value_query_string_parameters, response.related_entries)


