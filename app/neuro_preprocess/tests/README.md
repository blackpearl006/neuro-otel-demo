# Test Suite for neuro-preprocess

This directory contains unit and integration tests for the neuroimaging preprocessing pipeline.

## Test Structure

```
tests/
├── __init__.py
├── test_loader.py          # Unit tests for DataLoader stage
├── test_processor.py       # Unit tests for ImageProcessor stage
├── test_writer.py          # Unit tests for DataWriter stage
├── test_integration.py     # Integration tests for full pipeline
└── README.md              # This file
```

## Running Tests

### Run all tests
```bash
cd app/
pytest
```

### Run specific test file
```bash
pytest neuro_preprocess/tests/test_loader.py
```

### Run tests matching a pattern
```bash
pytest -k "test_loader"
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests with coverage
```bash
pytest --cov=neuro_preprocess --cov-report=html
```

### Run only unit tests
```bash
pytest -m unit
```

### Run only integration tests
```bash
pytest -m integration
```

## Test Categories

### Unit Tests
- `test_loader.py`: Tests for file loading functionality
  - File size calculation
  - Data shape validation
  - Metadata extraction
  - Input validation

- `test_processor.py`: Tests for image processing
  - Individual stage execution (skull strip, bias correction, normalization)
  - Timing measurements
  - Data transformations
  - Selective stage execution

- `test_writer.py`: Tests for output writing
  - File creation
  - Metadata JSON generation
  - Processing reports
  - Compression handling

### Integration Tests
- `test_integration.py`: End-to-end pipeline tests
  - Full pipeline execution
  - Batch processing
  - Telemetry integration (tracing, metrics)
  - Error handling
  - Statistics tracking

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov
```

Optional dependencies for enhanced testing:
```bash
pip install pytest-timeout pytest-xdist
```

## Writing New Tests

### Unit Test Template
```python
import pytest
from neuro_preprocess.stages.my_stage import MyStage

class TestMyStage:
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        return {...}

    def test_my_functionality(self, sample_data):
        """Test description"""
        stage = MyStage()
        result = stage.process(sample_data)
        assert result is not None
```

### Integration Test Template
```python
import pytest
from neuro_preprocess.pipeline import PreprocessingPipeline

class TestMyIntegration:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories"""
        import tempfile
        input_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        yield input_dir, output_dir
        # Cleanup
        import shutil
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)

    def test_pipeline_end_to_end(self, temp_dirs):
        """Test full pipeline"""
        input_dir, output_dir = temp_dirs
        # Create test file
        # Run pipeline
        # Assert results
```

## Continuous Integration

Tests should pass before merging:
```bash
# Run all tests
pytest

# Check coverage
pytest --cov=neuro_preprocess --cov-fail-under=70
```

## Troubleshooting

### Tests fail with "ModuleNotFoundError"
Make sure you've installed the package:
```bash
cd app/
pip install -e .
```

### Tests fail with OpenTelemetry errors
Some integration tests require OpenTelemetry. Install dependencies:
```bash
pip install -r requirements.txt
```

### Tests are slow
Use pytest-xdist for parallel execution:
```bash
pip install pytest-xdist
pytest -n auto
```

## Test Coverage Goals

- **Unit tests**: >80% coverage for individual modules
- **Integration tests**: Cover all major user workflows
- **Edge cases**: Test error handling and boundary conditions

## Related Documentation

- Main README: `../../../README.md`
- Layman docs: `../../../layman_docs/`
- Troubleshooting: `../../../layman_docs/05-troubleshooting.md`
