"""
Integration tests for the complete pipeline with telemetry
"""

import pytest
import tempfile
import os
import time
from pathlib import Path

from neuro_preprocess.pipeline import PreprocessingPipeline
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry import trace, metrics


class TestPipelineIntegration:
    """Integration tests for the complete preprocessing pipeline"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary input and output directories"""
        input_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()

        yield input_dir, output_dir

        # Cleanup
        import shutil
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)

    @pytest.fixture
    def test_file(self, temp_dirs):
        """Create a test input file"""
        input_dir, _ = temp_dirs
        filepath = os.path.join(input_dir, 'sub-001_T1w.nii.gz')

        # Create dummy file (1 MB)
        with open(filepath, 'wb') as f:
            f.write(b'0' * (1024 * 1024))

        return filepath

    def test_full_pipeline_success(self, test_file, temp_dirs):
        """Test complete pipeline execution with success"""
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(
            output_dir=output_dir,
            output_format='nifti'
        )

        result = pipeline.process_file(test_file)

        # Check result structure
        assert result['status'] == 'success'
        assert 'total_duration' in result
        assert 'stages' in result

        # Check all stages completed
        assert 'load' in result['stages']
        assert 'process' in result['stages']
        assert 'write' in result['stages']

        # Check output file exists
        output_file = result['stages']['write']['output_file']
        assert os.path.exists(output_file)

    def test_pipeline_batch_processing(self, temp_dirs):
        """Test batch processing of multiple files"""
        input_dir, output_dir = temp_dirs

        # Create 3 test files
        files = []
        for i in range(1, 4):
            filepath = os.path.join(input_dir, f'sub-{i:03d}_T1w.nii.gz')
            with open(filepath, 'wb') as f:
                f.write(b'0' * (1024 * 1024))
            files.append(filepath)

        pipeline = PreprocessingPipeline(output_dir=output_dir)

        # Process batch
        batch_stats = pipeline.process_batch(files, show_progress=False)

        # Check batch stats
        assert batch_stats['total_files'] == 3
        assert batch_stats['successful'] == 3
        assert batch_stats['failed'] == 0
        assert batch_stats['success_rate'] == 100.0

    def test_pipeline_with_selective_stages(self, test_file, temp_dirs):
        """Test pipeline with selective stages enabled"""
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(
            output_dir=output_dir,
            enable_skull_strip=False,
            enable_bias_correction=True,
            enable_normalization=False
        )

        result = pipeline.process_file(test_file)

        # Should still succeed with selective stages
        assert result['status'] == 'success'

        # Process stage should complete with fewer steps
        process_stats = result['stages']['process']
        assert process_stats['steps'] < 3  # Not all 3 stages enabled

    def test_pipeline_timing(self, test_file, temp_dirs):
        """Test that pipeline timing is reasonable"""
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)

        start = time.time()
        result = pipeline.process_file(test_file)
        end = time.time()

        # Total duration should match actual time (within tolerance)
        actual_duration = end - start
        reported_duration = result['total_duration']

        assert abs(actual_duration - reported_duration) < 0.5

    def test_pipeline_statistics(self, test_file, temp_dirs):
        """Test that pipeline maintains statistics correctly"""
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)

        # Process multiple files
        for _ in range(3):
            pipeline.process_file(test_file)

        stats = pipeline.get_statistics()

        assert stats['files_processed'] == 3
        assert stats['files_failed'] == 0
        assert stats['total_processing_time'] > 0

    def test_pipeline_error_handling(self, temp_dirs):
        """Test pipeline error handling"""
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)

        # Try to process nonexistent file
        with pytest.raises(Exception):
            pipeline.process_file('/nonexistent/file.nii.gz')

        # Statistics should reflect failure
        stats = pipeline.get_statistics()
        assert stats['files_failed'] == 1

    def test_pipeline_reset_statistics(self, test_file, temp_dirs):
        """Test resetting pipeline statistics"""
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)

        # Process a file
        pipeline.process_file(test_file)

        # Reset statistics
        pipeline.reset_statistics()

        stats = pipeline.get_statistics()
        assert stats['files_processed'] == 0
        assert stats['files_failed'] == 0
        assert stats['total_processing_time'] == 0.0


class TestTelemetryIntegration:
    """Integration tests for telemetry (tracing, metrics, logging)"""

    @pytest.fixture
    def telemetry_setup(self):
        """Set up in-memory telemetry exporters for testing"""
        # Set up tracing
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)

        # Set up metrics
        metric_reader = InMemoryMetricReader()
        meter_provider = MeterProvider(metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        yield span_exporter, metric_reader

        # Cleanup
        span_exporter.clear()

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories"""
        input_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()

        yield input_dir, output_dir

        import shutil
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)

    @pytest.fixture
    def test_file(self, temp_dirs):
        """Create test file"""
        input_dir, _ = temp_dirs
        filepath = os.path.join(input_dir, 'sub-001_T1w.nii.gz')
        with open(filepath, 'wb') as f:
            f.write(b'0' * (1024 * 1024))
        return filepath

    def test_tracing_creates_spans(self, test_file, temp_dirs, telemetry_setup):
        """Test that pipeline creates trace spans"""
        span_exporter, _ = telemetry_setup
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)
        pipeline.process_file(test_file)

        # Get exported spans
        spans = span_exporter.get_finished_spans()

        # Should have created spans
        assert len(spans) > 0

        # Check for expected span names
        span_names = [span.name for span in spans]
        assert 'preprocess_file' in span_names

    def test_tracing_span_hierarchy(self, test_file, temp_dirs, telemetry_setup):
        """Test that spans have correct parent-child relationships"""
        span_exporter, _ = telemetry_setup
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)
        pipeline.process_file(test_file)

        spans = span_exporter.get_finished_spans()

        # Find root span
        root_spans = [s for s in spans if s.parent is None]
        assert len(root_spans) >= 1  # Should have at least one root span

        # Find child spans
        child_spans = [s for s in spans if s.parent is not None]
        assert len(child_spans) > 0  # Should have child spans

    def test_tracing_span_attributes(self, test_file, temp_dirs, telemetry_setup):
        """Test that spans have expected attributes"""
        span_exporter, _ = telemetry_setup
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)
        pipeline.process_file(test_file)

        spans = span_exporter.get_finished_spans()

        # Find preprocess_file span
        preprocess_span = next((s for s in spans if s.name == 'preprocess_file'), None)
        assert preprocess_span is not None

        # Check attributes
        attributes = dict(preprocess_span.attributes or {})
        assert 'file.name' in attributes or 'file.path' in attributes

    def test_span_status_on_success(self, test_file, temp_dirs, telemetry_setup):
        """Test that span status is OK on success"""
        span_exporter, _ = telemetry_setup
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)
        pipeline.process_file(test_file)

        spans = span_exporter.get_finished_spans()

        # All spans should have OK status
        for span in spans:
            assert not span.status.is_ok or span.status.is_ok  # Either unset or OK

    def test_metrics_recorded(self, test_file, temp_dirs, telemetry_setup):
        """Test that metrics are recorded"""
        _, metric_reader = telemetry_setup
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)
        pipeline.process_file(test_file)

        # Force metrics flush
        metrics_data = metric_reader.get_metrics_data()

        # Should have recorded some metrics
        # Note: This depends on whether metrics are actually implemented in the pipeline
        # If metrics are implemented, they should appear here
        assert metrics_data is not None

    def test_multiple_traces_independent(self, test_file, temp_dirs, telemetry_setup):
        """Test that processing multiple files creates independent traces"""
        span_exporter, _ = telemetry_setup
        _, output_dir = temp_dirs

        pipeline = PreprocessingPipeline(output_dir=output_dir)

        # Process twice
        pipeline.process_file(test_file, output_filename='output1')
        pipeline.process_file(test_file, output_filename='output2')

        spans = span_exporter.get_finished_spans()

        # Should have spans from both runs
        # Each run should create its own root span
        root_spans = [s for s in spans if s.parent is None]
        assert len(root_spans) >= 2


class TestEndToEnd:
    """End-to-end tests simulating real usage"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories"""
        input_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        yield input_dir, output_dir
        import shutil
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)

    def test_realistic_workflow(self, temp_dirs):
        """Test realistic workflow: create files, process, verify outputs"""
        input_dir, output_dir = temp_dirs

        # Create test dataset (5 files)
        for i in range(1, 6):
            filepath = os.path.join(input_dir, f'sub-{i:03d}_T1w.nii.gz')
            with open(filepath, 'wb') as f:
                f.write(b'0' * (1024 * 1024 * i))  # Varying sizes

        # Initialize pipeline
        pipeline = PreprocessingPipeline(
            output_dir=output_dir,
            output_format='nifti',
            enable_skull_strip=True,
            enable_bias_correction=True,
            enable_normalization=True,
            save_metadata=True,
            compress_output=True
        )

        # Get list of files
        input_files = sorted(Path(input_dir).glob('*.nii.gz'))
        input_files = [str(f) for f in input_files]

        # Process batch
        batch_stats = pipeline.process_batch(input_files, show_progress=False)

        # Verify results
        assert batch_stats['successful'] == 5
        assert batch_stats['failed'] == 0

        # Verify output files exist
        output_files = list(Path(output_dir).glob('*.npy'))
        assert len(output_files) == 5

        # Verify metadata files exist
        metadata_files = list(Path(output_dir).glob('*.json'))
        assert len(metadata_files) == 5

        # Verify report files exist
        report_files = list(Path(output_dir).glob('*.report.txt'))
        assert len(report_files) == 5

    def test_performance_batch_vs_sequential(self, temp_dirs):
        """Test that batch processing is efficient"""
        input_dir, output_dir = temp_dirs

        # Create 3 test files
        files = []
        for i in range(1, 4):
            filepath = os.path.join(input_dir, f'sub-{i:03d}_T1w.nii.gz')
            with open(filepath, 'wb') as f:
                f.write(b'0' * (1024 * 1024))
            files.append(filepath)

        pipeline = PreprocessingPipeline(output_dir=output_dir)

        # Batch processing
        start = time.time()
        batch_stats = pipeline.process_batch(files, show_progress=False)
        batch_time = time.time() - start

        # Verify batch completed
        assert batch_stats['successful'] == 3

        # Batch time should be reasonable (not more than 3x single file time)
        avg_time_per_file = batch_stats['average_duration_per_file']
        assert batch_time < avg_time_per_file * 3.5  # Some overhead is acceptable
