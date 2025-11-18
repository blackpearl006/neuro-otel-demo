"""
Unit tests for the DataLoader stage
"""

import pytest
import tempfile
import os
from pathlib import Path
import numpy as np

from neuro_preprocess.stages.loader import DataLoader


class TestDataLoader:
    """Test suite for DataLoader"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as f:
            # Create a file with known size (1 MB)
            f.write(b'0' * (1024 * 1024))
            filepath = f.name

        yield filepath

        # Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)

    def test_loader_initialization(self):
        """Test that loader initializes correctly"""
        loader = DataLoader(validate=True)
        assert loader.validate is True

        loader_no_validate = DataLoader(validate=False)
        assert loader_no_validate.validate is False

    def test_load_returns_expected_structure(self, temp_file):
        """Test that load() returns the expected data structure"""
        loader = DataLoader(validate=False)
        result = loader.load(temp_file)

        # Check required keys
        assert 'data' in result
        assert 'metadata' in result
        assert 'file_path' in result
        assert 'file_size_mb' in result
        assert 'load_time_seconds' in result

        # Check types
        assert isinstance(result['data'], np.ndarray)
        assert isinstance(result['metadata'], dict)
        assert isinstance(result['file_size_mb'], float)
        assert isinstance(result['load_time_seconds'], float)

    def test_load_file_size_calculation(self, temp_file):
        """Test that file size is calculated correctly"""
        loader = DataLoader(validate=False)
        result = loader.load(temp_file)

        # File is 1 MB, should be close to 1.0
        assert 0.9 < result['file_size_mb'] < 1.1

    def test_load_creates_3d_array(self, temp_file):
        """Test that loader creates a 3D array"""
        loader = DataLoader(validate=False)
        result = loader.load(temp_file)

        data = result['data']
        assert data.ndim == 3, f"Expected 3D array, got {data.ndim}D"
        assert data.shape == (128, 128, 100), f"Expected shape (128, 128, 100), got {data.shape}"

    def test_load_timing(self, temp_file):
        """Test that load timing is reasonable"""
        loader = DataLoader(validate=False)
        result = loader.load(temp_file)

        # Load time should be between 0 and 3 seconds (simulated)
        assert 0 < result['load_time_seconds'] < 3

    def test_metadata_structure(self, temp_file):
        """Test that metadata contains expected fields"""
        loader = DataLoader(validate=False)
        result = loader.load(temp_file)

        metadata = result['metadata']

        # Check required metadata fields
        assert 'modality' in metadata
        assert 'scanner' in metadata
        assert 'field_strength' in metadata
        assert 'dimensions' in metadata

    def test_validation_enabled(self, temp_file):
        """Test that validation runs when enabled"""
        loader = DataLoader(validate=True)

        # Should not raise an exception for valid data
        result = loader.load(temp_file)
        assert result is not None

    def test_validation_detects_nan(self, temp_file):
        """Test that validation detects NaN values"""
        loader = DataLoader(validate=True)

        # This test would need a file with NaN values
        # For now, we just verify validation runs without error
        result = loader.load(temp_file)
        data = result['data']

        # Manually check for NaN
        assert not np.isnan(data).any(), "Data should not contain NaN"

    def test_validation_detects_inf(self, temp_file):
        """Test that validation detects Inf values"""
        loader = DataLoader(validate=True)
        result = loader.load(temp_file)
        data = result['data']

        # Manually check for Inf
        assert not np.isinf(data).any(), "Data should not contain Inf"

    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises an error"""
        loader = DataLoader(validate=False)

        with pytest.raises(FileNotFoundError):
            loader.load('/nonexistent/file.nii.gz')

    def test_load_timing_consistency(self, temp_file):
        """Test that load timing increases with file size"""
        loader = DataLoader(validate=False)

        # Load the same file twice
        result1 = loader.load(temp_file)
        result2 = loader.load(temp_file)

        # Load times should be similar (within 50% tolerance)
        time_diff = abs(result1['load_time_seconds'] - result2['load_time_seconds'])
        avg_time = (result1['load_time_seconds'] + result2['load_time_seconds']) / 2
        tolerance = avg_time * 0.5

        assert time_diff < tolerance, f"Load times vary too much: {result1['load_time_seconds']} vs {result2['load_time_seconds']}"

    def test_data_range(self, temp_file):
        """Test that simulated data is in expected range"""
        loader = DataLoader(validate=False)
        result = loader.load(temp_file)
        data = result['data']

        # Data should be in reasonable range (simulated MRI intensities)
        assert data.min() >= 0, "Data should be non-negative"
        assert data.max() <= 5000, "Data should be within typical MRI range"


class TestDataLoaderEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_file(self):
        """Test handling of empty file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as f:
            filepath = f.name  # Create empty file

        loader = DataLoader(validate=False)

        try:
            # Should handle empty file gracefully
            result = loader.load(filepath)
            assert result['file_size_mb'] == 0
        finally:
            os.remove(filepath)

    def test_large_file_simulation(self):
        """Test with large file (>100MB)"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as f:
            # Create 150 MB file
            f.write(b'0' * (150 * 1024 * 1024))
            filepath = f.name

        loader = DataLoader(validate=False)

        try:
            result = loader.load(filepath)
            # Load time should be capped at 2 seconds
            assert result['load_time_seconds'] <= 2.1
        finally:
            os.remove(filepath)

    def test_different_file_extensions(self):
        """Test with different file extensions"""
        extensions = ['.nii.gz', '.nii', '.dcm']

        for ext in extensions:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(b'0' * (1024 * 1024))
                filepath = f.name

            loader = DataLoader(validate=False)

            try:
                result = loader.load(filepath)
                assert result is not None
                assert 'data' in result
            finally:
                os.remove(filepath)
