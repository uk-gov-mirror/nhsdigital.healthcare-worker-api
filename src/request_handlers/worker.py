"""Handler for the worker endpoint"""
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.worker import FhirWorker, FhirIdentifier, FhirName
from ldap.connection import HcwLdapConnection
from logs.log import Log
from request_handlers.base_handler import BaseHandler

logger = Log("practitioner_handler")


class PractitionerHandler(BaseHandler):
    def __init__(self):
        self.ldap_connection = HcwLdapConnection()

    def get(self, event: APIGatewayProxyEvent) -> FhirWorker:
        logger.info("Performing practitioner GET")
        worker_id = event.query_string_parameters.get("identifier")

        nhs_person = self.ldap_connection.search_active_nhs_person(worker_id)

        worker = FhirWorker()
        worker.id = nhs_person.uid
        worker.resourceType = "Practitioner"
        worker.active = True
        worker.identifier = [FhirIdentifier("https://fhir.nhs.uk/Id/sds-user-id", nhs_person.uid)]
        worker.name = [FhirName(
            "usual",
            nhs_person.sn,
            f"{nhs_person.given_name} {nhs_person.nhs_middle_names}".strip(),
            nhs_person.personal_title
        )]

        logger.info("Returning worker from practitioner GET")
        return worker
