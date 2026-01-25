"""
OpenTelemetry configuration for Aspire Dashboard integration.

Exports logs and traces to the Aspire OTLP endpoint via HTTP/Protobuf.

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (set by Aspire)
    OTEL_SERVICE_NAME: Service name for telemetry (set by Aspire)
"""

from __future__ import annotations

import logging
import os
from contextlib import nullcontext
from typing import Any

_EXPORT_TIMEOUT_MS = 10000
_EXPORT_DELAY_MS = 1000
_MAX_EXPORT_BATCH_SIZE = 256


def _get_endpoint() -> str | None:
    return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")


def _get_service_name() -> str:
    return os.getenv("OTEL_SERVICE_NAME", "homunculy")


def _create_resource():
    from opentelemetry.sdk.resources import Resource

    return Resource.create(
        {
            "service.name": _get_service_name(),
            "service.instance.id": os.getenv("HOSTNAME", "local"),
        }
    )


def is_otlp_enabled() -> bool:
    return bool(_get_endpoint())


def configure_opentelemetry() -> None:
    """Configure OpenTelemetry HTTP/Protobuf exporters for Aspire Dashboard."""
    endpoint = _get_endpoint()
    if not endpoint:
        return

    try:
        logging.getLogger(__name__).info(
            "Configuring OpenTelemetry",
            extra={"endpoint": endpoint, "service": _get_service_name()},
        )
        _setup_logging(endpoint)
        _setup_tracing(endpoint)
        logging.getLogger(__name__).info("OpenTelemetry configured successfully")
    except ImportError as e:
        logging.getLogger(__name__).warning(
            "OpenTelemetry packages not available", extra={"error": str(e)}
        )
    except Exception as e:
        logging.getLogger(__name__).error(
            "Failed to configure OpenTelemetry", extra={"error": str(e)}
        )


def _setup_logging(endpoint: str) -> None:
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

    provider = LoggerProvider(resource=_create_resource())
    exporter = OTLPLogExporter(endpoint=f"{endpoint}/v1/logs", timeout=_EXPORT_TIMEOUT_MS)
    provider.add_log_record_processor(
        BatchLogRecordProcessor(
            exporter,
            schedule_delay_millis=_EXPORT_DELAY_MS,
            max_export_batch_size=_MAX_EXPORT_BATCH_SIZE,
        )
    )
    set_logger_provider(provider)
    logging.getLogger().addHandler(LoggingHandler(level=logging.DEBUG, logger_provider=provider))


def _setup_tracing(endpoint: str) -> None:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=_create_resource())
    exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", timeout=_EXPORT_TIMEOUT_MS)
    provider.add_span_processor(
        BatchSpanProcessor(
            exporter,
            schedule_delay_millis=_EXPORT_DELAY_MS,
            max_export_batch_size=_MAX_EXPORT_BATCH_SIZE,
        )
    )
    trace.set_tracer_provider(provider)


def get_tracer(name: str) -> Any:
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpTracer:
    def start_as_current_span(self, name: str, **kwargs: Any) -> Any:
        return nullcontext()
