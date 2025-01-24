import os
from unittest.mock import MagicMock, patch

import pytest

from fhir.fhir_object import FhirObject
from fhir.fhir_practitioner import FhirPractitioner
from request_handlers.handlers import RequestRouter, UnknownHandlerException


@patch.dict(os.environ, {"BASE_URL": "https://www.example.com/"})
@patch("request_handlers.handlers.PractitionerHandler")
def test_handler_practitioner(practitioner_handler):
    event = MagicMock()
    practitioner = MagicMock
    practitioner.url = "url"
    practitioner_handler.return_value.get.return_value.main_response = [practitioner]

    response = RequestRouter().handle_event("/Practitioner", event)

    assert list(response.entry)[0].resource == practitioner_handler.return_value.get.return_value.main_response[0]


@patch.dict(os.environ, {"BASE_URL": "https://www.example.com/"})
@patch("request_handlers.handlers.StatusHandler")
def test_handler_root(status_handler):
    event = MagicMock()
    status_response = MagicMock
    status_response.url = "url"
    status_handler.return_value.get.return_value.main_response = [status_response]

    response = RequestRouter().handle_event("/", event)

    assert list(response.entry)[0].resource == status_handler.return_value.get.return_value.main_response[0]


@patch.dict(os.environ, {"BASE_URL": "https://www.example.com/"})
@patch("request_handlers.handlers.StatusHandler")
def test_handler_status(status_handler):
    event = MagicMock()
    status_response = MagicMock
    status_response.url = "url"
    status_handler.return_value.get.return_value.main_response = [status_response]

    response = RequestRouter().handle_event("/_status", event)

    assert list(response.entry)[0].resource == status_handler.return_value.get.return_value.main_response[0]


@patch.dict(os.environ, {"BASE_URL": "https://www.example.com/"})
def test_handle_unknown_endpoint():
    with pytest.raises(UnknownHandlerException) as e:
        RequestRouter().handle_event("/UnknownEndpoint", MagicMock())

    assert e.value.status_code == 404
    assert e.value.fhir_code == "unknown"
    assert e.value.return_message == "There is no defined handler for the provided endpoint /UnknownEndpoint"

