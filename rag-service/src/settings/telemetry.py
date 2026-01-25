"""
OpenTelemetry configuration for Aspire Dashboard integration.

Exports logs, traces, and metrics to the Aspire OTLP endpoint for
centralized observability across all polyglot services.

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (set by Aspire)
    OTEL_SERVICE_NAME: Service name for telemetry (set by Aspire)
"""

from __future__ import annotations

import logging
import os
from contextlib import AbstractContextManager, nullcontext


def _get_otlp_endpoint() -> str | None:
    """Get OTLP endpoint from environment."""
    return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")


def _get_service_name() -> str:
    """Get service name from environment."""
    return os.getenv("OTEL_SERVICE_NAME", "rag-service")


def is_otlp_enabled() -> bool:
    """Check if OTLP export is enabled."""
    return bool(_get_otlp_endpoint())


def configure_opentelemetry() -> None:
    """
    Configure OpenTelemetry for Aspire Dashboard integration.

    Sets up:
    1. Log exporter - sends structured logs to Aspire
    2. Trace exporter - sends distributed traces
    3. Resource attributes for service identification

    Only activates if OTEL_EXPORTER_OTLP_ENDPOINT is set.
    """
    endpoint = _get_otlp_endpoint()
    if not endpoint:
        return

    try:
        _setup_otel_logging(endpoint)
        _setup_otel_tracing(endpoint)
        logging.getLogger(__name__).info(
            "OpenTelemetry configured",
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
    """Configure OpenTelemetry log exporter."""
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
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
    exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

    set_logger_provider(logger_provider)

    handler = LoggingHandler(level=logging.DEBUG, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)


def _setup_otel_tracing(endpoint: str) -> None:
    """Configure OpenTelemetry trace exporter."""
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
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
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


def get_tracer(name: str) -> object:
    """Get a tracer instance for distributed tracing."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpTracer:
    """No-op tracer when OpenTelemetry is not available."""

    def start_as_current_span(self, name: str, **kwargs: object) -> AbstractContextManager[None]:
        """Return a no-op context manager."""
        return nullcontext()
