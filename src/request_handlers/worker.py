"""Handler for the worker endpoint"""
import os
from datetime import datetime, timedelta
from typing import Optional

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_worker import FhirWorker, FhirIdentifier, FhirName
from hcw_exception import HcwException
from ldap.connection import HcwLdapConnection
from logs.log import Log
from request_handlers.base_handler import BaseHandler

logger = Log("practitioner_handler")

# Creating the connection here means that it's saved between requests, meaning that we don't need to re-establish
# the LDAP connection on every request.
ldap_connection: Optional[HcwLdapConnection] = None
if "UNIT_TESTING" not in os.environ:
    # Unfortunately doing this during unit testing is difficult because it triggers during the import before we have
    # any mocking. But having it here moves the initial connection creation to the lambda start instead of the first
    # request, which greatly improves performance for that request if we have provisioned concurrency.
    ldap_connection = HcwLdapConnection()


class PractitionerHandler(BaseHandler):
    def __init__(self):
        global ldap_connection
        if not ldap_connection or ldap_connection.connection.closed or ldap_connection.bind_time < datetime.now() - timedelta(minutes=5):
            logger.info("Creating new ldap connection instance")
            ldap_connection = HcwLdapConnection()
        else:
            logger.info("Using existing LDAP connection instance")

    def get(self, event: APIGatewayProxyEvent) -> FhirWorker:
        logger.info("Performing practitioner GET")
        worker_id = event.query_string_parameters.get("identifier")

        if not worker_id:
            raise HcwException(400, "Missing practitioner identifier")

        nhs_person = ldap_connection.search_active_nhs_person(worker_id)

        if nhs_person.nhs_person_status != "1":
            raise HcwException(400, "User inactive")

        worker = FhirWorker()
        worker.id = nhs_person.uid
        worker.resourceType = "Practitioner"
        worker.active = True
        worker.identifier = [FhirIdentifier("https://fhir.nhs.uk/Id/sds-user-id", nhs_person.uid)]
        worker.name = [FhirName(
            "usual",
            nhs_person.sn,
            f"{str(nhs_person.given_name or '')} {str(nhs_person.nhs_middle_names or '')}".strip(),
            nhs_person.personal_title
        )]

        logger.info("Returning worker from practitioner GET")
        return worker
