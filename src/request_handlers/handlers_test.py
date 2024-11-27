from unittest.mock import MagicMock, patch

import pytest

from request_handlers.handlers import RequestRouter, UnknownHandlerException


@patch("request_handlers.handlers.PractitionerHandler")
def test_handler_practitioner(practitioner_handler):
    event = MagicMock()

    response = RequestRouter().handle_event("/Practitioner", event)

    assert response == practitioner_handler.return_value.get.return_value


@patch("request_handlers.handlers.StatusHandler")
def test_handler_root(status_handler):
    event = MagicMock()

    response = RequestRouter().handle_event("/", event)

    assert response == status_handler.return_value.get.return_value


@patch("request_handlers.handlers.StatusHandler")
def test_handler_status(status_handler):
    event = MagicMock()

    response = RequestRouter().handle_event("/_status", event)

    assert response == status_handler.return_value.get.return_value


def test_handle_unknown_endpoint():
    with pytest.raises(UnknownHandlerException) as e:
        RequestRouter().handle_event("/UnknownEndpoint", MagicMock())

    assert e.value.status_code == 404
    assert e.value.return_message == "There is no defined handler for the provided endpoint /UnknownEndpoint"

