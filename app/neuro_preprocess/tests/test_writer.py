"""
Unit tests for the DataWriter stage
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
import numpy as np

from neuro_preprocess.stages.writer import DataWriter


class TestDataWriter:
    """Test suite for DataWriter"""

    @pytest.fixture
    def sample_processed_data(self):
        """Create sample processed data"""
        return {
            'data': np.random.randn(128, 128, 100),
            'metadata': {
                'modality': 'T1-weighted MRI',
                'scanner': 'Siemens Prisma',
                'field_strength': '3T',
                'dimensions': '(128, 128, 100)',
                'processing_date': '2025-11-19'
            },
            'file_path': '/test/scan.nii.gz',
            'file_size_mb': 5.2,
            'processing_stats': {
                'total_processing_time': 1.3,
                'steps_completed': 3,
                'skull_strip': {'duration': 0.7},
                'bias_correction': {'duration': 0.5},
                'normalization': {'duration': 0.1}
            }
        }

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup (remove all files in temp dir)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_writer_initialization(self):
        """Test writer initialization with different formats"""
        writer_nifti = DataWriter(output_format='nifti')
        assert writer_nifti.output_format == 'nifti'

        writer_mgz = DataWriter(output_format='mgz')
        assert writer_mgz.output_format == 'mgz'

        writer_analyze = DataWriter(output_format='analyze')
        assert writer_analyze.output_format == 'analyze'

    def test_write_returns_expected_structure(self, sample_processed_data, temp_dir):
        """Test that write() returns expected structure"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path)

        # Check required keys
        assert 'output_file' in result
        assert 'write_time_seconds' in result
        assert 'file_size_kb' in result

    def test_write_creates_output_file(self, sample_processed_data, temp_dir):
        """Test that write creates the output file"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path)

        # Check file exists
        assert os.path.exists(result['output_file'])

    def test_write_creates_metadata_json(self, sample_processed_data, temp_dir):
        """Test that write creates metadata JSON file"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path, save_metadata=True)

        # Check metadata file exists
        metadata_file = result['output_file'].replace('.npy', '.json')
        assert os.path.exists(metadata_file)

        # Check metadata content
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            assert 'modality' in metadata
            assert 'processing_date' in metadata

    def test_write_creates_report(self, sample_processed_data, temp_dir):
        """Test that write creates processing report"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path)

        # Check report file exists
        report_file = result['output_file'].replace('.npy', '.report.txt')
        assert os.path.exists(report_file)

        # Check report content
        with open(report_file, 'r') as f:
            report_content = f.read()
            assert 'Processing Report' in report_content
            assert 'Total Processing Time' in report_content

    def test_write_with_compression(self, sample_processed_data, temp_dir):
        """Test writing with compression enabled"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path, compress=True)

        # File should exist
        assert os.path.exists(result['output_file'])

    def test_write_without_compression(self, sample_processed_data, temp_dir):
        """Test writing without compression"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path, compress=False)

        # File should exist
        assert os.path.exists(result['output_file'])

    def test_write_timing(self, sample_processed_data, temp_dir):
        """Test that write timing is reasonable"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path)

        # Write time should be between 0 and 3 seconds (simulated)
        assert 0 < result['write_time_seconds'] < 3

    def test_write_file_size(self, sample_processed_data, temp_dir):
        """Test that file size is calculated"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path)

        # File size should be positive
        assert result['file_size_kb'] > 0

    def test_write_creates_directory(self, sample_processed_data, temp_dir):
        """Test that write creates output directory if it doesn't exist"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'subdir', 'output')

        result = writer.write(sample_processed_data, output_path)

        # Directory should be created
        assert os.path.exists(os.path.dirname(result['output_file']))

    def test_write_without_create_dirs_fails(self, sample_processed_data, temp_dir):
        """Test that write fails if directory doesn't exist and create_dirs=False"""
        writer = DataWriter(output_format='nifti', create_dirs=False)
        output_path = os.path.join(temp_dir, 'nonexistent', 'output')

        with pytest.raises(Exception):
            writer.write(sample_processed_data, output_path)

    def test_write_different_formats(self, sample_processed_data, temp_dir):
        """Test writing in different formats"""
        formats = ['nifti', 'mgz', 'analyze']

        for fmt in formats:
            writer = DataWriter(output_format=fmt, create_dirs=True)
            output_path = os.path.join(temp_dir, f'output_{fmt}')

            result = writer.write(sample_processed_data, output_path)

            # File should exist
            assert os.path.exists(result['output_file'])

    def test_metadata_json_structure(self, sample_processed_data, temp_dir):
        """Test metadata JSON has correct structure"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path, save_metadata=True)

        metadata_file = result['output_file'].replace('.npy', '.json')

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

            # Check required fields
            assert 'modality' in metadata
            assert 'output_path' in metadata
            assert 'original_input' in metadata
            assert 'processing_statistics' in metadata

    def test_report_content(self, sample_processed_data, temp_dir):
        """Test processing report content"""
        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(sample_processed_data, output_path)

        report_file = result['output_file'].replace('.npy', '.report.txt')

        with open(report_file, 'r') as f:
            content = f.read()

            # Check report contains key information
            assert 'Total Processing Time' in content
            assert 'Steps Completed' in content
            assert 'Output File' in content


class TestDataWriterEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_write_overwrites_existing(self, temp_dir):
        """Test that writing overwrites existing files"""
        data = {
            'data': np.random.randn(128, 128, 100),
            'metadata': {'modality': 'T1w'},
            'processing_stats': {'total_processing_time': 1.0, 'steps_completed': 1}
        }

        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        # Write first time
        result1 = writer.write(data, output_path)

        # Write second time (should overwrite)
        result2 = writer.write(data, output_path)

        # Both should succeed
        assert os.path.exists(result1['output_file'])
        assert os.path.exists(result2['output_file'])
        assert result1['output_file'] == result2['output_file']

    def test_write_with_empty_metadata(self, temp_dir):
        """Test writing with minimal metadata"""
        data = {
            'data': np.random.randn(128, 128, 100),
            'metadata': {},  # Empty metadata
            'processing_stats': {'total_processing_time': 1.0, 'steps_completed': 0}
        }

        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        # Should handle gracefully
        result = writer.write(data, output_path)
        assert os.path.exists(result['output_file'])

    def test_write_without_metadata_flag(self, temp_dir):
        """Test that metadata file is not created when save_metadata=False"""
        data = {
            'data': np.random.randn(128, 128, 100),
            'metadata': {'modality': 'T1w'},
            'processing_stats': {'total_processing_time': 1.0, 'steps_completed': 1}
        }

        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(data, output_path, save_metadata=False)

        # Metadata file should NOT exist
        metadata_file = result['output_file'].replace('.npy', '.json')
        assert not os.path.exists(metadata_file)

    def test_write_large_array(self, temp_dir):
        """Test writing large data array"""
        # Create larger array (256x256x200)
        data = {
            'data': np.random.randn(256, 256, 200),
            'metadata': {'modality': 'T1w'},
            'processing_stats': {'total_processing_time': 1.0, 'steps_completed': 1}
        }

        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output')

        result = writer.write(data, output_path)

        # Should handle large array
        assert os.path.exists(result['output_file'])
        assert result['file_size_kb'] > 0

    def test_write_special_characters_in_path(self, temp_dir):
        """Test writing with special characters in path"""
        data = {
            'data': np.random.randn(128, 128, 100),
            'metadata': {'modality': 'T1w'},
            'processing_stats': {'total_processing_time': 1.0, 'steps_completed': 1}
        }

        writer = DataWriter(output_format='nifti', create_dirs=True)
        output_path = os.path.join(temp_dir, 'output_test-123')

        result = writer.write(data, output_path)
        assert os.path.exists(result['output_file'])

    def test_write_timing_consistency(self, temp_dir):
        """Test that write timing is consistent"""
        data = {
            'data': np.random.randn(128, 128, 100),
            'metadata': {'modality': 'T1w'},
            'processing_stats': {'total_processing_time': 1.0, 'steps_completed': 1}
        }

        writer = DataWriter(output_format='nifti', create_dirs=True)

        times = []
        for i in range(3):
            output_path = os.path.join(temp_dir, f'output_{i}')
            result = writer.write(data, output_path)
            times.append(result['write_time_seconds'])

        # All times should be similar (within 50% tolerance)
        avg_time = sum(times) / len(times)
        for t in times:
            assert abs(t - avg_time) < avg_time * 0.5
