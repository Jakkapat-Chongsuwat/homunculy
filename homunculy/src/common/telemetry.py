"""
OpenTelemetry configuration for Aspire Dashboard integration.

Exports logs and traces to the Aspire OTLP endpoint via HTTP/protobuf.
gRPC is not used due to certificate issues with local development.

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (set by Aspire)
    OTEL_SERVICE_NAME: Service name for telemetry (set by Aspire)
"""

from __future__ import annotations

import logging
import os
from contextlib import nullcontext
from typing import Any

# Export settings - tuned for local dev resilience
_EXPORT_TIMEOUT_MS = 10000  # 10s timeout
_EXPORT_DELAY_MS = 5000  # 5s delay between batches (let collector start)
_MAX_EXPORT_BATCH_SIZE = 256


def _get_otlp_endpoint() -> str | None:
    """Get OTLP endpoint from environment, with http default if no scheme."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return None
    # Only add http scheme if none provided
    if not endpoint.startswith(("http://", "https://")):
        return f"http://{endpoint}"
    return endpoint


def _get_service_name() -> str:
    """Get service name from environment."""
    return os.getenv("OTEL_SERVICE_NAME", "homunculy")


def is_otlp_enabled() -> bool:
    """Check if OTLP export is enabled."""
    return bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))


def configure_opentelemetry() -> None:
    """
    Configure OpenTelemetry for Aspire Dashboard integration.

    Uses HTTP/protobuf protocol only (no gRPC) for reliable local dev.
    Only activates if OTEL_EXPORTER_OTLP_ENDPOINT is set.
    """
    endpoint = _get_otlp_endpoint()
    if not endpoint:
        return

    try:
        _setup_otel_logging(endpoint)
        _setup_otel_tracing(endpoint)
        logging.getLogger(__name__).info(
            "OpenTelemetry configured (HTTP)",
            extra={"endpoint": endpoint, "service": _get_service_name()},
        )
    except ImportError as e:
        logging.getLogger(__name__).warning(
            "OpenTelemetry packages not available",
            extra={"error": str(e)},
        )
    except Exception as e:
        logging.getLogger(__name__).error(
            "Failed to configure OpenTelemetry",
            extra={"error": str(e)},
        )


def _setup_otel_logging(endpoint: str) -> None:
    """Configure OpenTelemetry log exporter via HTTP."""
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    resource = Resource.create(
        {
            "service.name": _get_service_name(),
            "service.instance.id": os.getenv("HOSTNAME", "local"),
        }
    )

    logger_provider = LoggerProvider(resource=resource)
    exporter = OTLPLogExporter(
        endpoint=f"{endpoint}/v1/logs",
        timeout=_EXPORT_TIMEOUT_MS,
    )
    processor = BatchLogRecordProcessor(
        exporter,
        schedule_delay_millis=_EXPORT_DELAY_MS,
        max_export_batch_size=_MAX_EXPORT_BATCH_SIZE,
    )
    logger_provider.add_log_record_processor(processor)

    set_logger_provider(logger_provider)

    handler = LoggingHandler(level=logging.DEBUG, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)


def _setup_otel_tracing(endpoint: str) -> None:
    """Configure OpenTelemetry trace exporter via HTTP."""
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": _get_service_name(),
            "service.instance.id": os.getenv("HOSTNAME", "local"),
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
        timeout=_EXPORT_TIMEOUT_MS,
    )
    processor = BatchSpanProcessor(
        exporter,
        schedule_delay_millis=_EXPORT_DELAY_MS,
        max_export_batch_size=_MAX_EXPORT_BATCH_SIZE,
    )
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


def get_tracer(name: str) -> Any:
    """Get a tracer instance for distributed tracing."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpTracer:
    """No-op tracer when OpenTelemetry is not available."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> Any:
        """Return a no-op context manager."""
        return nullcontext()
