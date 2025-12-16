"""
OpenTelemetry Telemetry Configuration
Exports setup functions for tracing, metrics, and logging
"""

from neuro_preprocess.telemetry.tracer_setup import setup_tracing, get_tracer
from neuro_preprocess.telemetry.metrics_setup import (
    setup_metrics,
    get_meter,
    create_pipeline_metrics,
)
from neuro_preprocess.telemetry.logger_setup import setup_logging, get_logger, log_with_trace, get_logger_provider, cleanup_logging

__all__ = [
    "setup_tracing",
    "get_tracer",
    "setup_metrics",
    "get_meter",
    "create_pipeline_metrics",
    "setup_logging",
    "get_logger",
    "log_with_trace",
    "get_logger_provider",
    "cleanup_logging",
]
