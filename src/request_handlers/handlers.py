from typing import Dict, Type

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_worker import FhirWorker
from hcw_exception import HcwException
from request_handlers.base_handler import BaseHandler
from request_handlers.status import StatusHandler
from request_handlers.worker import PractitionerHandler


class UnknownHandlerException(HcwException):
    def __init__(self, endpoint):
        super().__init__(404, f"There is no defined handler for the provided endpoint {endpoint}")


class RequestRouter:
    handlers: Dict[str, Type[BaseHandler]]

    def __init__(self):
        self.handlers = {
            "/Practitioner": PractitionerHandler,
            "/": StatusHandler,
            "/_status": StatusHandler
        }

    def handle_event(self, endpoint: str, event: APIGatewayProxyEvent) -> FhirWorker:
        if endpoint not in self.handlers:
            raise UnknownHandlerException(endpoint)

        return self.handlers[endpoint]().get(event)

