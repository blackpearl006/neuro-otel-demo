"""
Command-Line Interface for the neuroimaging preprocessing pipeline
"""

import sys
import os
from pathlib import Path
from typing import List
import click

from neuro_preprocess.pipeline import PreprocessingPipeline
from neuro_preprocess.telemetry import setup_tracing, setup_metrics, setup_logging


def initialize_telemetry():
    """Initialize OpenTelemetry tracing, metrics, and logging"""
    # Check if telemetry is enabled (default: enabled)
    if os.getenv("OTEL_SDK_DISABLED", "false").lower() == "true":
        click.echo("⚠ OpenTelemetry disabled via OTEL_SDK_DISABLED")
        return

    try:
        # Get OTLP endpoint from environment
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

        # Initialize telemetry
        setup_tracing(otlp_endpoint=otlp_endpoint)
        setup_metrics(otlp_endpoint=otlp_endpoint)
        setup_logging(otlp_endpoint=otlp_endpoint)

        click.echo(f"✓ OpenTelemetry enabled → {otlp_endpoint}\n")
    except Exception as e:
        click.echo(click.style(f"⚠ Warning: Could not initialize OpenTelemetry: {e}", fg="yellow"))
        click.echo("  Continuing without telemetry...\n")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Neuroimaging Preprocessing Pipeline with OpenTelemetry"""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    default="./output",
    type=click.Path(),
    help="Output directory for processed files",
)
@click.option(
    "--output-name",
    "-n",
    default=None,
    help="Output filename (auto-generated if not specified)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    default="nifti",
    type=click.Choice(["nifti", "mgz", "analyze"]),
    help="Output file format",
)
@click.option(
    "--no-skull-strip",
    is_flag=True,
    help="Disable skull stripping",
)
@click.option(
    "--no-bias-correction",
    is_flag=True,
    help="Disable bias field correction",
)
@click.option(
    "--no-normalization",
    is_flag=True,
    help="Disable intensity normalization",
)
@click.option(
    "--no-validate",
    is_flag=True,
    help="Skip input validation",
)
@click.option(
    "--no-metadata",
    is_flag=True,
    help="Don't save metadata JSON",
)
@click.option(
    "--no-compress",
    is_flag=True,
    help="Don't compress output files",
)
def process(
    input_file,
    output_dir,
    output_name,
    output_format,
    no_skull_strip,
    no_bias_correction,
    no_normalization,
    no_validate,
    no_metadata,
    no_compress,
):
    """Process a single neuroimaging file"""

    click.echo(f"\n🧠 Neuroimaging Preprocessing Pipeline")
    click.echo(f"{'=' * 50}\n")

    # Initialize OpenTelemetry
    initialize_telemetry()

    # Initialize pipeline
    pipeline = PreprocessingPipeline(
        output_dir=output_dir,
        output_format=output_format,
        enable_skull_strip=not no_skull_strip,
        enable_bias_correction=not no_bias_correction,
        enable_normalization=not no_normalization,
        validate_inputs=not no_validate,
        save_metadata=not no_metadata,
        compress_output=not no_compress,
    )

    # Process file
    try:
        result = pipeline.process_file(input_file, output_filename=output_name)

        # Display results
        click.echo(click.style("✓ Processing completed successfully!", fg="green", bold=True))
        click.echo(f"\nOutput file: {result['stages']['write']['output_file']}")
        click.echo(f"Total time: {result['total_duration']:.2f}s")

        # Display stage details
        click.echo(f"\nStage breakdown:")
        for stage, stats in result['stages'].items():
            click.echo(f"  {stage}: {stats.get('duration', 0):.2f}s")

        return 0

    except Exception as e:
        click.echo(click.style(f"✗ Processing failed: {e}", fg="red", bold=True), err=True)
        return 1


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--output-dir",
    "-o",
    default="./output",
    type=click.Path(),
    help="Output directory for processed files",
)
@click.option(
    "--pattern",
    "-p",
    default="*.nii*",
    help="File pattern to match (e.g., '*.nii.gz')",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    default="nifti",
    type=click.Choice(["nifti", "mgz", "analyze"]),
    help="Output file format",
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Don't show progress bar",
)
@click.option(
    "--no-skull-strip",
    is_flag=True,
    help="Disable skull stripping",
)
@click.option(
    "--no-bias-correction",
    is_flag=True,
    help="Disable bias field correction",
)
@click.option(
    "--no-normalization",
    is_flag=True,
    help="Disable intensity normalization",
)
def batch(
    input_dir,
    output_dir,
    pattern,
    output_format,
    no_progress,
    no_skull_strip,
    no_bias_correction,
    no_normalization,
):
    """Process multiple files in a directory"""

    click.echo(f"\n🧠 Batch Neuroimaging Preprocessing")
    click.echo(f"{'=' * 50}\n")

    # Initialize OpenTelemetry
    initialize_telemetry()

    # Find input files
    input_path = Path(input_dir)
    input_files = list(input_path.glob(pattern))

    if not input_files:
        click.echo(
            click.style(f"No files found matching pattern '{pattern}' in {input_dir}", fg="yellow"),
            err=True,
        )
        return 1

    click.echo(f"Found {len(input_files)} file(s) matching pattern '{pattern}'")

    # Initialize pipeline
    pipeline = PreprocessingPipeline(
        output_dir=output_dir,
        output_format=output_format,
        enable_skull_strip=not no_skull_strip,
        enable_bias_correction=not no_bias_correction,
        enable_normalization=not no_normalization,
    )

    # Process batch
    try:
        batch_stats = pipeline.process_batch(
            [str(f) for f in input_files],
            show_progress=not no_progress,
        )

        if batch_stats["failed"] > 0:
            return 1
        else:
            return 0

    except Exception as e:
        click.echo(click.style(f"✗ Batch processing failed: {e}", fg="red", bold=True), err=True)
        return 1


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
def info(input_file):
    """Display information about a neuroimaging file"""

    click.echo(f"\n📊 File Information")
    click.echo(f"{'=' * 50}\n")

    try:
        from neuro_preprocess.stages.loader import DataLoader

        loader = DataLoader(validate=False)
        data = loader.load(input_file)

        click.echo(f"File: {input_file}")
        click.echo(f"Size: {data['file_size_mb']:.2f} MB")
        click.echo(f"Shape: {data['data'].shape}")
        click.echo(f"Data type: {data['data'].dtype}")

        click.echo(f"\nMetadata:")
        for key, value in data['metadata'].items():
            click.echo(f"  {key}: {value}")

        return 0

    except Exception as e:
        click.echo(click.style(f"✗ Failed to read file: {e}", fg="red", bold=True), err=True)
        return 1


def main():
    """Entry point for the CLI"""
    sys.exit(cli())


if __name__ == "__main__":
    main()
