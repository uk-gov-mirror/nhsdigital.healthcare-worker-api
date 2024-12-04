from abc import abstractmethod

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from fhir.fhir_object import FhirObject
from fhir.fhir_practitioner import FhirPractitioner


class HandlerResponse[T]:
    """
    Type for responses coming back from data source. The related entries contain references to our main response,
    the caller of the API might have requested some of the related entries via a _revinclude query parameter. So
    we're returning all related entries here and letting the FHIR layer work out if they're relevant.

    These entries were included in the search results anyway, and so there's very little performance overhead to
    them being passed up through the layers. This helps to keep the layers separate, with the data fetching
    not needing to know the full details of the FHIR request.
    """
    main_response: list[T]
    related_entries: list

    def __init__(self, main_response: list[T], related_entries: list):
        self.main_response = main_response
        self.related_entries = related_entries


class BaseHandler[T]:
    @abstractmethod
    def get(self, event: APIGatewayProxyEvent) -> HandlerResponse[T]:
        pass
