"""Handler for the worker endpoint"""
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_practitioner import FhirPractitioner
from fhir.fhir_practitioner_role import FhirPractitionerRole
from hcw_exception import HcwException
from ldap.connection_fetch import get_connection
from logs.log import Log
from request_handlers.base_handler import BaseHandler, HandlerResponse

logger = Log("practitioner_handler")


class PractitionerHandler(BaseHandler[FhirPractitioner]):
    def get(self, event: APIGatewayProxyEvent) -> HandlerResponse[FhirPractitioner]:
        logger.info("Performing practitioner GET", "REQ_PRACT_START")
        worker_id = event.query_string_parameters.get("identifier")

        if not worker_id:
            raise HcwException(400, "Missing practitioner identifier", "invalid")

        nhs_person, org_persons, org_roles = get_connection().search_active_nhs_person(worker_id)

        if nhs_person.nhs_person_status != "1":
            raise HcwException(400, "User inactive", "business-rule")

        practitioner = FhirPractitioner(nhs_person)
        practitioner_roles = [FhirPractitionerRole(nhs_person, org_role) for org_role in org_roles]

        logger.info("Returning worker from practitioner GET","REQ_PRACT_SUCCESS")

        return HandlerResponse([practitioner], practitioner_roles)
