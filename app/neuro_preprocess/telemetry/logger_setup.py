"""
OpenTelemetry Logger Setup
Configures structured logging with trace correlation
"""

import logging
import os
from opentelemetry import trace
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION


def setup_logging(
    service_name: str = "neuro-preprocess",
    service_version: str = "0.1.0",
    otlp_endpoint: str = None,
    log_level: int = logging.INFO,
) -> logging.Logger:
    """
    Initialize OpenTelemetry logging with trace correlation

    Args:
        service_name: Name of this service
        service_version: Version of this service
        otlp_endpoint: OTLP collector endpoint (default: from env or localhost:4317)
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    # Get OTLP endpoint from environment or use default
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    # Create resource with service information
    resource = Resource(
        attributes={
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # Create logger provider
    logger_provider = LoggerProvider(resource=resource)

    # Configure OTLP exporter
    otlp_exporter = OTLPLogExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # For local development (use TLS in production)
    )

    # Add log processor with batching
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

    # Create OpenTelemetry logging handler
    handler = LoggingHandler(
        level=log_level,
        logger_provider=logger_provider,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Also add console handler for local visibility
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Create application logger
    logger = logging.getLogger("neuro_preprocess")

    print(f"✓ Logging initialized: {service_name} → {otlp_endpoint}")

    return logger


def get_logger(name: str = "neuro_preprocess") -> logging.Logger:
    """
    Get a logger instance with trace correlation

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_trace(logger: logging.Logger, level: int, message: str, **kwargs):
    """
    Log a message with current trace context

    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **kwargs: Additional fields to include in log
    """
    # Get current span context
    span = trace.get_current_span()
    span_context = span.get_span_context()

    # Add trace ID and span ID to extra fields
    extra = {
        "trace_id": format(span_context.trace_id, '032x') if span_context.is_valid else "0",
        "span_id": format(span_context.span_id, '016x') if span_context.is_valid else "0",
        **kwargs,
    }

    logger.log(level, message, extra=extra)
