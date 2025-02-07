from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_practitioner_role import FhirPractitionerRole
from hcw_exception import HcwException
from ldap.connection_fetch import get_connection
from logs.log import Log
from request_handlers.base_handler import BaseHandler, HandlerResponse

logger = Log("practitioner_role_handler")


class PractitionerRoleHandler(BaseHandler[FhirPractitionerRole]):
    def get(self, event: APIGatewayProxyEvent) -> HandlerResponse[FhirPractitionerRole]:
        logger.info("Performing practitioner role GET")
        if "practitioner.identifier" in event.query_string_parameters:
            worker_id = event.query_string_parameters.get("practitioner.identifier")
            practitioner, _org_persons, roles = get_connection().search_active_nhs_person(worker_id)

            fhir_roles = [FhirPractitionerRole(practitioner, pr) for pr in roles]

            logger.info("Returning worker from practitioner role GET from practitioner ID")
            return HandlerResponse(fhir_roles, [])
        elif "identifier" in event.query_string_parameters:
            # This functionality will be covered under HCW-163
            pass
        else:
            raise HcwException(400, "MISSING_VALUE", "Query filters missing", "unknown")


