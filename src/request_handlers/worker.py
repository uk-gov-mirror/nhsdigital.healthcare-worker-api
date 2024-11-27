"""Handler for the worker endpoint"""
import os
from datetime import datetime, timedelta
from typing import Optional

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_worker import FhirWorker, FhirIdentifier, FhirName
from hcw_exception import HcwException
from ldap.connection_fetch import get_connection
from logs.log import Log
from request_handlers.base_handler import BaseHandler

logger = Log("practitioner_handler")


class PractitionerHandler(BaseHandler):
    def get(self, event: APIGatewayProxyEvent) -> FhirWorker:
        logger.info("Performing practitioner GET")
        worker_id = event.query_string_parameters.get("identifier")

        if not worker_id:
            raise HcwException(400, "Missing practitioner identifier")

        nhs_person = get_connection().search_active_nhs_person(worker_id)

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
