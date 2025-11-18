"""
OpenTelemetry Metrics Setup
Configures custom metrics for the preprocessing pipeline
"""

import os
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION


def setup_metrics(
    service_name: str = "neuro-preprocess",
    service_version: str = "0.1.0",
    otlp_endpoint: str = None,
    export_interval_millis: int = 10000,  # Export every 10 seconds
) -> metrics.Meter:
    """
    Initialize OpenTelemetry metrics

    Args:
        service_name: Name of this service
        service_version: Version of this service
        otlp_endpoint: OTLP collector endpoint (default: from env or localhost:4317)
        export_interval_millis: How often to export metrics (milliseconds)

    Returns:
        Configured meter instance
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

    # Configure OTLP exporter
    otlp_exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # For local development (use TLS in production)
    )

    # Create periodic exporting metric reader
    metric_reader = PeriodicExportingMetricReader(
        otlp_exporter,
        export_interval_millis=export_interval_millis,
    )

    # Create meter provider
    provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    # Set as global meter provider
    metrics.set_meter_provider(provider)

    # Create and return meter
    meter = metrics.get_meter(__name__)

    print(f"✓ Metrics initialized: {service_name} → {otlp_endpoint}")

    return meter


def get_meter(name: str = "neuro-preprocess") -> metrics.Meter:
    """
    Get a meter instance

    Args:
        name: Instrumentation name

    Returns:
        Meter instance
    """
    return metrics.get_meter(name)


def create_pipeline_metrics(meter: metrics.Meter) -> dict:
    """
    Create common metrics for the preprocessing pipeline

    Args:
        meter: Meter instance

    Returns:
        Dictionary of metric instruments
    """
    return {
        # Counters
        "files_processed": meter.create_counter(
            name="neuro.files.processed",
            description="Number of files processed",
            unit="files",
        ),
        "files_failed": meter.create_counter(
            name="neuro.files.failed",
            description="Number of files that failed processing",
            unit="files",
        ),
        "processing_errors": meter.create_counter(
            name="neuro.processing.errors",
            description="Number of processing errors",
            unit="errors",
        ),
        # Histograms
        "file_size": meter.create_histogram(
            name="neuro.file.size",
            description="Size of input files",
            unit="MB",
        ),
        "load_duration": meter.create_histogram(
            name="neuro.stage.load.duration",
            description="Time spent loading data",
            unit="s",
        ),
        "process_duration": meter.create_histogram(
            name="neuro.stage.process.duration",
            description="Time spent processing data",
            unit="s",
        ),
        "write_duration": meter.create_histogram(
            name="neuro.stage.write.duration",
            description="Time spent writing output",
            unit="s",
        ),
        "total_duration": meter.create_histogram(
            name="neuro.pipeline.duration",
            description="Total pipeline execution time",
            unit="s",
        ),
        "voxels_processed": meter.create_histogram(
            name="neuro.voxels.processed",
            description="Number of voxels processed",
            unit="voxels",
        ),
        "compression_ratio": meter.create_histogram(
            name="neuro.compression.ratio",
            description="Compression ratio of output files",
            unit="ratio",
        ),
    }
