from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_status import FhirStatus
from request_handlers.base_handler import BaseHandler, HandlerResponse


class StatusHandler(BaseHandler[FhirStatus]):
    def get(self, event: APIGatewayProxyEvent) -> HandlerResponse[FhirStatus]:
        return HandlerResponse([FhirStatus(True)], [])
