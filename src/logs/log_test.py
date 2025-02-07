from unittest.mock import patch, MagicMock

import logs.log
from logs.log import Log


@patch("logs.log.logging")
def test_log_init(logging):
    Log("test_module")

    logging.getLogger.assert_called_with("test_module")
    logging.getLogger.return_value.setLevel.assert_called_with(logging.INFO)


@patch("logs.log.uuid4")
def test_log_save_details(uuid4_mock):
    logger = Log("test_module")
    event = MagicMock()

    logger.save_event_details(event)

    event.resolved_headers_field.get.assert_called_with("X-Correlation-ID", [f"no-id-{uuid4_mock.return_value}"])
    assert logs.log.correlation_id == event.resolved_headers_field.get.return_value.__getitem__.return_value


def test_log_cleanup():
    logger = Log("test_module")
    logs.log.correlation_id = "correlation_id"

    logger.cleanup()

    assert logs.log.correlation_id is None


@patch("logs.log.logging")
def test_log_info(logging):
    logger = Log("test_module")
    logs.log.correlation_id = "correlation_id"

    logger.info("logging message")

    logging.getLogger.return_value.info.assert_called_with({"Correlation-ID": "correlation_id", "message": "logging message"})


@patch("logs.log.logging")
def test_log_error(logging):
    logger = Log("test_module")
    logs.log.correlation_id = "correlation_id"

    logger.error("logging message")

    logging.getLogger.return_value.error.assert_called_with({"Correlation-ID": "correlation_id", "message": "logging message"})
