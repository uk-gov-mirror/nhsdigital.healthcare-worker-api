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
        logger.info("Performing practitioner GET")
        
        # Log query parameters
        logger.info(f"Query parameters: {event.query_string_parameters}")
        
        worker_id = event.query_string_parameters.get("identifier")
        logger.info(f"Worker ID from query parameters: {worker_id}")

        if not worker_id:
            logger.error("Missing practitioner identifier in request")
            raise HcwException(400, "Missing practitioner identifier", "invalid")

        logger.info(f"Getting LDAP connection for worker ID: {worker_id}")
        try:
            connection = get_connection()
            logger.info("Successfully got LDAP connection")
            
            logger.info(f"Searching for NHS person with ID: {worker_id}")
            nhs_person, org_persons, org_roles = connection.search_active_nhs_person(worker_id)
            logger.info(f"Successfully retrieved NHS person: {nhs_person.uid}, {nhs_person.given_name} {nhs_person.sn}")

            if nhs_person.nhs_person_status != "1":
                logger.warning(f"User {worker_id} is inactive (status: {nhs_person.nhs_person_status})")
                raise HcwException(400, "User inactive", "business-rule")

            logger.info("Creating FHIR Practitioner resource")
            practitioner = FhirPractitioner(nhs_person)
            
            logger.info(f"Creating FHIR PractitionerRole resources for {len(org_roles)} roles")
            practitioner_roles = [FhirPractitionerRole(nhs_person, org_role) for org_role in org_roles]
            logger.info(f"Created {len(practitioner_roles)} PractitionerRole resources")

            logger.info("Returning worker from practitioner GET")
            return HandlerResponse([practitioner], practitioner_roles)
            
        except Exception as e:
            logger.error(f"Error in practitioner GET: {e}")
            raise
