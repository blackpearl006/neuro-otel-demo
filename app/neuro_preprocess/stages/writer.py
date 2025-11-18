"""
Writer Stage - Saves processed neuroimaging data
Represents writing output files in various formats (NIfTI, BIDS, etc.)
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from opentelemetry import trace

# Get tracer
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


class DataWriter:
    """Writes processed neuroimaging data to disk"""

    def __init__(self, output_format: str = "nifti", create_dirs: bool = True):
        """
        Initialize the data writer

        Args:
            output_format: Output file format ('nifti', 'mgz', etc.)
            create_dirs: Whether to create output directories if they don't exist
        """
        self.output_format = output_format
        self.create_dirs = create_dirs
        self.supported_formats = ['nifti', 'mgz', 'analyze']

        if output_format not in self.supported_formats:
            raise ValueError(
                f"Unsupported format '{output_format}'. "
                f"Supported: {', '.join(self.supported_formats)}"
            )

    def write(
        self,
        image_data: Dict[str, Any],
        output_path: str,
        save_metadata: bool = True,
        compress: bool = True,
    ) -> Dict[str, Any]:
        """
        Write processed image data to disk

        Args:
            image_data: Dictionary containing processed image and metadata
            output_path: Path where to save the output file
            save_metadata: Whether to save metadata as separate JSON file
            compress: Whether to compress the output (if format supports it)

        Returns:
            Dictionary with write statistics

        Raises:
            IOError: If writing fails
        """
        with tracer.start_as_current_span("write_output") as span:
            path = Path(output_path)

            span.set_attribute("output.path", str(path))
            span.set_attribute("output.format", self.output_format)
            span.set_attribute("compress", compress)
            logger.info(f"Writing output to: {path.name}")

            # Create output directory if needed
            if self.create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data for writing
            data = image_data["data"]
            metadata = image_data.get("metadata", {})
            processing_stats = image_data.get("processing_stats", {})

            # Write image data
            write_stats = self._write_image(data, path, compress=compress)
            span.set_attribute("output.size_kb", write_stats["file_size_kb"])

            # Write metadata if requested
            if save_metadata:
                metadata_path = path.with_suffix('.json')
                metadata_stats = self._write_metadata(
                    metadata, processing_stats, metadata_path
                )
                write_stats["metadata_file"] = str(metadata_path)
                write_stats["metadata_size_kb"] = metadata_stats["size_kb"]

            # Create processing report
            if processing_stats:
                report_path = path.with_suffix('.report.txt')
                self._write_processing_report(processing_stats, report_path)
                write_stats["report_file"] = str(report_path)

            logger.info(f"Successfully wrote {path.name}")
            return write_stats

    def _write_image(
        self, data: np.ndarray, path: Path, compress: bool = True
    ) -> Dict[str, Any]:
        """
        Write image data to file

        In real scenario: nibabel.save(nifti_img, path)
        """
        start_time = time.time()

        # Determine file extension
        if self.output_format == 'nifti':
            if compress:
                output_file = path.with_suffix('.nii.gz')
            else:
                output_file = path.with_suffix('.nii')
        elif self.output_format == 'mgz':
            output_file = path.with_suffix('.mgz')
        else:
            output_file = path.with_suffix('.img')  # Analyze format

        # Simulate writing time (depends on data size and compression)
        data_size_mb = data.nbytes / (1024 * 1024)
        write_time = min(0.2 + (data_size_mb / 50), 3.0)

        if compress:
            write_time *= 1.5  # Compression takes longer

        time.sleep(write_time)

        # Actually write data (simplified - just save as numpy for demo)
        try:
            # In real scenario: would use nibabel or similar
            # For demo: save as .npy for easy verification
            np.save(str(output_file.with_suffix('.npy')), data)

            # Create dummy output file with original extension
            output_file.touch()

            file_size_kb = output_file.stat().st_size / 1024
            if compress:
                file_size_kb = data_size_mb * 1024 * 0.3  # Simulated compression ratio

        except IOError as e:
            raise IOError(f"Failed to write image to {output_file}: {e}")

        stats = {
            "output_file": str(output_file),
            "format": self.output_format,
            "compressed": compress,
            "data_shape": data.shape,
            "data_dtype": str(data.dtype),
            "file_size_kb": file_size_kb,
            "original_size_mb": data_size_mb,
            "compression_ratio": data_size_mb * 1024 / file_size_kb if compress else 1.0,
            "write_time_seconds": time.time() - start_time,
        }

        return stats

    def _write_metadata(
        self,
        metadata: Dict[str, Any],
        processing_stats: Dict[str, Any],
        path: Path,
    ) -> Dict[str, Any]:
        """Write metadata and processing stats to JSON file"""
        start_time = time.time()

        combined_metadata = {
            "original_metadata": metadata,
            "processing_statistics": processing_stats,
            "output_metadata": {
                "format": self.output_format,
                "generated_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

        try:
            with open(path, 'w') as f:
                json.dump(combined_metadata, f, indent=2, default=str)

            file_size_kb = path.stat().st_size / 1024

        except IOError as e:
            raise IOError(f"Failed to write metadata to {path}: {e}")

        return {
            "size_kb": file_size_kb,
            "write_time_seconds": time.time() - start_time,
        }

    def _write_processing_report(
        self, processing_stats: Dict[str, Any], path: Path
    ) -> None:
        """Generate a human-readable processing report"""
        try:
            with open(path, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("NEUROIMAGING PROCESSING REPORT\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Input information
                f.write("INPUT DATA:\n")
                f.write(f"  Shape: {processing_stats.get('input_shape', 'N/A')}\n")
                f.write(f"  Data type: {processing_stats.get('input_dtype', 'N/A')}\n\n")

                # Processing steps
                f.write("PROCESSING STEPS:\n")
                steps = processing_stats.get('steps_completed', [])
                for i, step in enumerate(steps, 1):
                    f.write(f"  {i}. {step.replace('_', ' ').title()}\n")

                    step_stats = processing_stats.get(step, {})
                    if 'processing_time' in step_stats:
                        f.write(f"     Time: {step_stats['processing_time']:.3f}s\n")

                    if 'method' in step_stats:
                        f.write(f"     Method: {step_stats['method']}\n")

                f.write(f"\nTotal processing time: "
                        f"{processing_stats.get('total_processing_time', 0):.3f}s\n")

                f.write("\n" + "=" * 60 + "\n")

        except IOError as e:
            # Don't fail the whole pipeline if report writing fails
            print(f"Warning: Could not write processing report: {e}")

    def validate_output(self, output_path: str) -> bool:
        """
        Validate that output file was written correctly

        Args:
            output_path: Path to the output file

        Returns:
            True if file exists and is valid
        """
        path = Path(output_path)

        # Check main file exists
        if not path.exists():
            return False

        # Check file is not empty
        if path.stat().st_size == 0:
            return False

        # Additional format-specific validation could go here
        return True
