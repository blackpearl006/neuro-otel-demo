"""
OpenTelemetry Tracer Setup
Configures distributed tracing for the preprocessing pipeline
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION


def setup_tracing(
    service_name: str = "neuro-preprocess",
    service_version: str = "0.1.0",
    otlp_endpoint: str = None,
) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing

    Args:
        service_name: Name of this service
        service_version: Version of this service
        otlp_endpoint: OTLP collector endpoint (default: from env or localhost:4317)

    Returns:
        Configured tracer instance
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

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # For local development (use TLS in production)
    )

    # Add span processor with batching
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Create and return tracer
    tracer = trace.get_tracer(__name__)

    print(f"✓ Tracing initialized: {service_name} → {otlp_endpoint}")

    return tracer


def get_tracer(name: str = "neuro-preprocess") -> trace.Tracer:
    """
    Get a tracer instance

    Args:
        name: Instrumentation name

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)
