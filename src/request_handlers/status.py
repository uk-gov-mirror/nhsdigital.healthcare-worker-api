from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_status import FhirStatus
from request_handlers.base_handler import BaseHandler


class StatusHandler(BaseHandler):
    def get(self, event: APIGatewayProxyEvent) -> FhirStatus:
        return FhirStatus(True)
