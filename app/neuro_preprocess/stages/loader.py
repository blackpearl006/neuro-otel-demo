"""
Data Loader Stage - Simulates loading neuroimaging data
Represents reading DICOM, NIfTI, or other medical imaging formats
"""

import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from opentelemetry import trace
from opentelemetry import metrics

# Get tracer and meter
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
logger = logging.getLogger(__name__)

# Create metrics
file_size_metric = meter.create_histogram(
    name="neuro.load.file_size",
    description="Size of loaded files",
    unit="MB",
)
load_duration_metric = meter.create_histogram(
    name="neuro.load.duration",
    description="Time to load files",
    unit="s",
)


class DataLoader:
    """Loads neuroimaging data files (simulated)"""

    def __init__(self, validate: bool = True):
        """
        Initialize the data loader

        Args:
            validate: Whether to perform validation checks on loaded data
        """
        self.validate = validate
        self.supported_formats = ['.nii', '.nii.gz', '.dcm', '.mgz']

    def load(self, file_path: str) -> Dict[str, Any]:
        """
        Load a neuroimaging file

        Args:
            file_path: Path to the imaging file

        Returns:
            Dictionary containing image data and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        # Create a span for the entire load operation
        with tracer.start_as_current_span("load_file") as span:
            path = Path(file_path)

            # Add span attributes
            span.set_attribute("file.name", path.name)
            span.set_attribute("file.path", str(path))

            logger.info(f"Loading file: {path.name}")

            # Check if file exists
            if not path.exists():
                span.set_attribute("error", True)
                span.add_event("File not found")
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check file format
            if not any(str(path).endswith(fmt) for fmt in self.supported_formats):
                span.set_attribute("error", True)
                span.add_event("Unsupported format")
                logger.error(f"Unsupported format: {path.suffix}")
                raise ValueError(
                    f"Unsupported format. Supported: {', '.join(self.supported_formats)}"
                )

            # Simulate file reading time (varies by size)
            file_size_mb = path.stat().st_size / (1024 * 1024)
            load_time = min(0.1 + (file_size_mb / 100), 2.0)  # 0.1-2 seconds

            # Record metrics
            file_size_metric.record(file_size_mb, {"file.format": path.suffix})
            span.set_attribute("file.size_mb", file_size_mb)

            logger.debug(f"File size: {file_size_mb:.2f} MB")

            time.sleep(load_time)

            # Simulate loading 3D neuroimaging data
            # Real scenario: would use nibabel, pydicom, etc.
            data = self._simulate_image_data(file_size_mb)
            metadata = self._extract_metadata(path)

            span.set_attribute("image.shape", str(data.shape))
            span.set_attribute("image.dtype", str(data.dtype))
            span.set_attribute("metadata.modality", metadata["modality"])

            if self.validate:
                with tracer.start_as_current_span("validate_data"):
                    self._validate_data(data, metadata)
                    logger.debug("Data validation passed")

            # Record load duration metric
            load_duration_metric.record(load_time, {
                "file.format": path.suffix,
                "modality": metadata["modality"],
            })

            logger.info(f"Successfully loaded {path.name} in {load_time:.2f}s")
            span.set_attribute("load.duration_seconds", load_time)
            span.set_status(trace.Status(trace.StatusCode.OK))

            return {
                "data": data,
                "metadata": metadata,
                "file_path": str(path),
                "file_size_mb": file_size_mb,
                "load_time_seconds": load_time,
            }

    def _simulate_image_data(self, file_size_mb: float) -> np.ndarray:
        """
        Simulate loading 3D imaging data

        In real scenario: nibabel.load(file_path).get_fdata()
        """
        # Estimate dimensions based on file size
        # Typical brain MRI: 256x256x170 = ~11M voxels
        if file_size_mb < 10:
            shape = (128, 128, 100)  # Small scan
        elif file_size_mb < 50:
            shape = (256, 256, 170)  # Standard brain MRI
        else:
            shape = (512, 512, 200)  # High-resolution scan

        # Create dummy data (in real scenario, this would be actual voxel intensities)
        # Using random sparse data to save memory
        data = np.random.randn(*shape).astype(np.float32) * 100

        return data

    def _extract_metadata(self, path: Path) -> Dict[str, Any]:
        """
        Extract metadata from file

        In real scenario: would extract DICOM tags, NIfTI headers, etc.
        """
        return {
            "filename": path.name,
            "format": path.suffix,
            "modality": self._guess_modality(path.name),
            "dimensions": "3D",
            "patient_id": f"SUB-{random.randint(1000, 9999)}",  # Simulated
            "session": f"ses-{random.randint(1, 5)}",
            "acquisition_date": "2024-01-15",  # Simulated
        }

    def _guess_modality(self, filename: str) -> str:
        """Guess imaging modality from filename"""
        filename_lower = filename.lower()
        if 't1w' in filename_lower or 't1' in filename_lower:
            return "T1-weighted MRI"
        elif 't2w' in filename_lower or 't2' in filename_lower:
            return "T2-weighted MRI"
        elif 'fmri' in filename_lower or 'bold' in filename_lower:
            return "functional MRI"
        elif 'dwi' in filename_lower or 'dti' in filename_lower:
            return "Diffusion MRI"
        else:
            return "Unknown"

    def _validate_data(self, data: np.ndarray, metadata: Dict[str, Any]) -> None:
        """
        Validate loaded data

        Raises:
            ValueError: If data is invalid
        """
        # Check for NaN or Inf values
        if np.isnan(data).any():
            raise ValueError("Data contains NaN values")

        if np.isinf(data).any():
            raise ValueError("Data contains Inf values")

        # Check dimensions
        if data.ndim != 3:
            raise ValueError(f"Expected 3D data, got {data.ndim}D")

        # Check if data is empty
        if data.size == 0:
            raise ValueError("Data is empty")

        # Simulate occasional validation failures (for testing error handling)
        if random.random() < 0.01:  # 1% chance of simulated error
            raise ValueError("Simulated validation failure: corrupted data detected")
