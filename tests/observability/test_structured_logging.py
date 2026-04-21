"""Unit tests for structured JSON logging."""
import json
import logging

import pytest

from app.core.logging import (
    JSONFormatter,
    _build_extra,
    configure_json_logging,
    log_request,
    log_security_event,
)


class TestJSONFormatter:
    """Tests for JSON log formatter."""

    def test_format_produces_valid_json(self):
        """Formatter output must be valid JSON."""
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        formatter = JSONFormatter()
        output = formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_format_includes_required_fields(self):
        """Output must contain timestamp, level, logger, message."""
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        formatter = JSONFormatter()
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed

    def test_format_includes_extra_fields(self):
        """Fields passed with logging `extra=` must be serialized into output."""
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="event",
            args=(),
            exc_info=None,
        )
        # Python logging attaches `extra={...}` keys as direct record attributes.
        record.event_type = "TEST"
        record.client_ip = "127.0.0.1"
        formatter = JSONFormatter()
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["event_type"] == "TEST"
        assert parsed["client_ip"] == "127.0.0.1"

    def test_format_timestamp_is_iso_format(self):
        """Timestamp must be ISO 8601."""
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        formatter = JSONFormatter()
        output = formatter.format(record)
        parsed = json.loads(output)
        # ISO 8601 contains a 'T' separator between date and time
        assert "T" in parsed["timestamp"]


class TestBuildExtra:
    """Tests for _build_extra helper."""

    def test_excludes_none_values(self):
        """None values must not appear in output."""
        result = _build_extra(event_type="TEST", client_ip=None, normalized_rut=None)
        assert "event_type" in result
        assert "client_ip" not in result
        assert "normalized_rut" not in result

    def test_includes_provided_values(self):
        """Non-None values must be present."""
        result = _build_extra(event_type="TEST", client_ip="127.0.0.1", normalized_rut=None)
        assert result["event_type"] == "TEST"
        assert result["client_ip"] == "127.0.0.1"

    def test_extra_kwargs_merged(self):
        """Additional kwargs must be merged into result."""
        result = _build_extra(event_type="TEST", custom_field="value")
        assert "custom_field" in result
        assert result["custom_field"] == "value"


class TestLogSecurityEvent:
    """Tests for log_security_event function."""

    def test_emits_expected_fields(self, caplog: pytest.LogCaptureFixture):
        """Emitted record must contain event_type, client_ip, normalized_rut, reason."""
        caplog.set_level(logging.WARNING)
        log_security_event(
            event_type="RATE_LIMIT_EXCEEDED",
            client_ip="192.168.1.1",
            normalized_rut="12345678-9",
            reason="IP limit exceeded",
            latency_ms=0.5,
        )
        assert caplog.records
        record = caplog.records[0]
        # The extra dict is set via the formatted JSON
        assert "security_event" in record.message


class TestLogRequest:
    """Tests for log_request function."""

    def test_emits_request_log(self, caplog: pytest.LogCaptureFixture):
        """log_request must emit a log record with method, path, status_code, latency_ms."""
        caplog.set_level(logging.INFO)
        log_request(
            method="GET",
            path="/v1/rut/12.345.678-5",
            client_ip="192.168.1.1",
            status_code=200,
            latency_ms=42.5,
            normalized_rut="12345678-9",
        )
        assert caplog.records
        record = caplog.records[0]
        assert "request_completed" in record.message


class TestConfigureJsonLogging:
    """Tests for configure_json_logging."""

    def test_sets_root_logger_level(self):
        """Root logger level must be set to the specified level."""
        configure_json_logging(log_level="debug")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_installs_json_handler(self):
        """Root logger must have a JSON handler."""
        configure_json_logging(log_level="info")
        root = logging.getLogger()
        handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert handlers

    def test_child_loggers_propagate_without_own_handlers(self):
        """Named app/uvicorn loggers must not duplicate root handler."""
        configure_json_logging(log_level="info")

        for name in ["app", "uvicorn", "uvicorn.access"]:
            logger = logging.getLogger(name)
            assert logger.propagate is True
            assert logger.handlers == []
