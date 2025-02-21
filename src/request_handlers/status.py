from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_status import FhirStatus
from ldap.connection_fetch import get_connection
from logs.log import Log
from request_handlers.base_handler import BaseHandler, HandlerResponse

logger = Log("StatusHandler")

class StatusHandler(BaseHandler[FhirStatus]):
    def get(self, event: APIGatewayProxyEvent) -> HandlerResponse[FhirStatus]:
        try:
            get_connection()
        except Exception as e:
            logger.error(f"Could not fetch ldap connection in status connection, returned error {e}")
            return HandlerResponse([FhirStatus(False)], [])
        return HandlerResponse([FhirStatus(True)], [])
