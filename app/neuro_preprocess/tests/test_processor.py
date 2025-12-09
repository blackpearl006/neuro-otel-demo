"""
Unit tests for the ImageProcessor stage
"""

import pytest
import numpy as np
from neuro_preprocess.stages.processor import ImageProcessor


class TestImageProcessor:
    """Test suite for ImageProcessor"""

    @pytest.fixture
    def sample_data(self):
        """Create sample image data"""
        return {
            'data': np.random.randn(128, 128, 100) * 100 + 500,
            'metadata': {
                'modality': 'T1-weighted MRI',
                'scanner': 'Siemens Prisma',
                'field_strength': '3T',
                'dimensions': '(128, 128, 100)'
            },
            'file_path': '/test/scan.nii.gz',
            'file_size_mb': 5.2,
            'load_time_seconds': 0.15
        }

    def test_processor_initialization_all_enabled(self):
        """Test processor with all stages enabled"""
        processor = ImageProcessor(
            enable_skull_strip=True,
            enable_bias_correction=True,
            enable_normalization=True
        )

        assert processor.enable_skull_strip is True
        assert processor.enable_bias_correction is True
        assert processor.enable_normalization is True

    def test_processor_initialization_selective(self):
        """Test processor with selective stages"""
        processor = ImageProcessor(
            enable_skull_strip=False,
            enable_bias_correction=True,
            enable_normalization=False
        )

        assert processor.enable_skull_strip is False
        assert processor.enable_bias_correction is True
        assert processor.enable_normalization is False

    def test_process_returns_expected_structure(self, sample_data):
        """Test that process() returns expected structure"""
        processor = ImageProcessor()
        result = processor.process(sample_data)

        # Check required keys
        assert 'data' in result
        assert 'metadata' in result
        assert 'processing_stats' in result

        # Check processing stats structure
        stats = result['processing_stats']
        assert 'total_processing_time' in stats
        assert 'steps_completed' in stats

    def test_process_all_stages_enabled(self, sample_data):
        """Test processing with all stages enabled"""
        processor = ImageProcessor(
            enable_skull_strip=True,
            enable_bias_correction=True,
            enable_normalization=True
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Should complete 3 steps
        assert stats['steps_completed'] == 3
        assert 'skull_strip' in stats
        assert 'bias_correction' in stats
        assert 'normalization' in stats

    def test_process_selective_stages(self, sample_data):
        """Test processing with selective stages"""
        processor = ImageProcessor(
            enable_skull_strip=True,
            enable_bias_correction=False,
            enable_normalization=True
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Should complete 2 steps (skull_strip and normalization)
        assert stats['steps_completed'] == 2
        assert 'skull_strip' in stats
        assert 'bias_correction' not in stats
        assert 'normalization' in stats

    def test_process_no_stages(self, sample_data):
        """Test processing with all stages disabled"""
        processor = ImageProcessor(
            enable_skull_strip=False,
            enable_bias_correction=False,
            enable_normalization=False
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Should complete 0 steps
        assert stats['steps_completed'] == 0

    def test_skull_strip_timing(self, sample_data):
        """Test skull stripping timing"""
        processor = ImageProcessor(
            enable_skull_strip=True,
            enable_bias_correction=False,
            enable_normalization=False
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Skull strip should take ~0.7 seconds
        assert 0.5 < stats['skull_strip']['duration'] < 1.0

    def test_bias_correction_timing(self, sample_data):
        """Test bias correction timing"""
        processor = ImageProcessor(
            enable_skull_strip=False,
            enable_bias_correction=True,
            enable_normalization=False
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Bias correction should take ~0.5 seconds
        assert 0.3 < stats['bias_correction']['duration'] < 0.8

    def test_normalization_timing(self, sample_data):
        """Test normalization timing"""
        processor = ImageProcessor(
            enable_skull_strip=False,
            enable_bias_correction=False,
            enable_normalization=True
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Normalization should take ~0.1 seconds
        assert 0.05 < stats['normalization']['duration'] < 0.3

    def test_total_processing_time(self, sample_data):
        """Test total processing time calculation"""
        processor = ImageProcessor(
            enable_skull_strip=True,
            enable_bias_correction=True,
            enable_normalization=True
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Total time should be sum of individual stages
        expected_time = (
            stats['skull_strip']['duration'] +
            stats['bias_correction']['duration'] +
            stats['normalization']['duration']
        )

        # Allow small tolerance for timing measurements
        assert abs(stats['total_processing_time'] - expected_time) < 0.1

    def test_data_shape_preserved(self, sample_data):
        """Test that data shape is preserved through processing"""
        processor = ImageProcessor()
        original_shape = sample_data['data'].shape

        result = processor.process(sample_data)
        processed_shape = result['data'].shape

        assert original_shape == processed_shape

    def test_metadata_preserved(self, sample_data):
        """Test that metadata is preserved"""
        processor = ImageProcessor()
        original_metadata = sample_data['metadata'].copy()

        result = processor.process(sample_data)

        # Original metadata should still be present
        for key in original_metadata:
            assert key in result['metadata']

    def test_metadata_updated(self, sample_data):
        """Test that metadata is updated with processing info"""
        processor = ImageProcessor()
        result = processor.process(sample_data)

        metadata = result['metadata']

        # Should have processing-related metadata
        assert 'processing_date' in metadata

    def test_skull_strip_reduces_volume(self, sample_data):
        """Test that skull stripping reduces data volume"""
        processor = ImageProcessor(
            enable_skull_strip=True,
            enable_bias_correction=False,
            enable_normalization=False
        )

        result = processor.process(sample_data)
        stats = result['processing_stats']

        # Should report voxels removed
        assert 'voxels_removed' in stats['skull_strip']
        assert stats['skull_strip']['voxels_removed'] > 0

    def test_normalization_scales_data(self, sample_data):
        """Test that normalization scales data appropriately"""
        processor = ImageProcessor(
            enable_skull_strip=False,
            enable_bias_correction=False,
            enable_normalization=True
        )

        result = processor.process(sample_data)
        data = result['data']

        # After normalization, data should be in [0, 1] range
        assert data.min() >= 0
        assert data.max() <= 1.0

    def test_process_handles_different_shapes(self):
        """Test processing with different data shapes"""
        shapes = [
            (64, 64, 50),
            (128, 128, 100),
            (256, 256, 200)
        ]

        processor = ImageProcessor()

        for shape in shapes:
            data = {
                'data': np.random.randn(*shape) * 100 + 500,
                'metadata': {'modality': 'T1w'},
                'file_path': '/test.nii.gz',
                'file_size_mb': 5.0,
                'load_time_seconds': 0.1
            }

            result = processor.process(data)
            assert result['data'].shape == shape


class TestImageProcessorEdgeCases:
    """Test edge cases and error handling"""

    def test_process_with_zeros(self):
        """Test processing data that's all zeros"""
        data = {
            'data': np.zeros((128, 128, 100)),
            'metadata': {'modality': 'T1w'},
            'file_path': '/test.nii.gz',
            'file_size_mb': 5.0,
            'load_time_seconds': 0.1
        }

        processor = ImageProcessor()
        result = processor.process(data)

        # Should handle gracefully
        assert result is not None
        assert 'data' in result

    def test_process_with_negative_values(self):
        """Test processing data with negative values"""
        data = {
            'data': np.random.randn(128, 128, 100) * 100 - 50,  # Some negative
            'metadata': {'modality': 'T1w'},
            'file_path': '/test.nii.gz',
            'file_size_mb': 5.0,
            'load_time_seconds': 0.1
        }

        processor = ImageProcessor()
        result = processor.process(data)

        # Should handle negative values
        assert result is not None

    def test_process_timing_consistency(self):
        """Test that processing timing is consistent"""
        data = {
            'data': np.random.randn(128, 128, 100) * 100 + 500,
            'metadata': {'modality': 'T1w'},
            'file_path': '/test.nii.gz',
            'file_size_mb': 5.0,
            'load_time_seconds': 0.1
        }

        processor = ImageProcessor(
            enable_skull_strip=True,
            enable_bias_correction=False,
            enable_normalization=False
        )

        # Run multiple times
        times = []
        for _ in range(3):
            result = processor.process(data.copy())
            times.append(result['processing_stats']['skull_strip']['duration'])

        # All times should be similar (within 50% tolerance)
        avg_time = sum(times) / len(times)
        for t in times:
            assert abs(t - avg_time) < avg_time * 0.5

    def test_process_preserves_input(self):
        """Test that processing doesn't modify input data"""
        data = {
            'data': np.random.randn(128, 128, 100) * 100 + 500,
            'metadata': {'modality': 'T1w'},
            'file_path': '/test.nii.gz',
            'file_size_mb': 5.0,
            'load_time_seconds': 0.1
        }

        original_data = data['data'].copy()
        processor = ImageProcessor()
        result = processor.process(data)

        # Original data should be unchanged
        np.testing.assert_array_equal(data['data'], original_data)
