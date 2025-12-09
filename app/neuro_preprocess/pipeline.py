"""
Preprocessing Pipeline - Orchestrates the complete workflow
Coordinates data loading, processing, and writing stages
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from tqdm import tqdm
from opentelemetry import trace

from neuro_preprocess.stages.loader import DataLoader
from neuro_preprocess.stages.processor import ImageProcessor
from neuro_preprocess.stages.writer import DataWriter
from neuro_preprocess.telemetry.metrics_setup import create_pipeline_metrics, get_meter

# Get tracer
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)
meter = get_meter(__name__)


class PreprocessingPipeline:
    """Main preprocessing pipeline orchestrator"""

    def __init__(
        self,
        output_dir: str = "./output",
        output_format: str = "nifti",
        enable_skull_strip: bool = True,
        enable_bias_correction: bool = True,
        enable_normalization: bool = True,
        validate_inputs: bool = True,
        save_metadata: bool = True,
        compress_output: bool = True,
    ):
        """
        Initialize the preprocessing pipeline

        Args:
            output_dir: Directory to save processed files
            output_format: Output file format ('nifti', 'mgz', etc.)
            enable_skull_strip: Enable skull stripping
            enable_bias_correction: Enable bias field correction
            enable_normalization: Enable intensity normalization
            validate_inputs: Validate input data
            save_metadata: Save metadata as JSON
            compress_output: Compress output files
        """
        self.output_dir = Path(output_dir)
        self.output_format = output_format

        # Initialize pipeline stages
        self.loader = DataLoader(validate=validate_inputs)
        self.processor = ImageProcessor(
            enable_skull_strip=enable_skull_strip,
            enable_bias_correction=enable_bias_correction,
            enable_normalization=enable_normalization,
        )
        self.writer = DataWriter(
            output_format=output_format,
            create_dirs=True,
        )

        # Configuration
        self.save_metadata = save_metadata
        self.compress_output = compress_output

        # Statistics
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "total_processing_time": 0.0,
            "errors": [],
        }

        # Initialize metrics
        self.metrics = create_pipeline_metrics(meter)

    def process_file(self, input_path: str, output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single neuroimaging file

        Args:
            input_path: Path to input file
            output_filename: Optional output filename (auto-generated if None)

        Returns:
            Dictionary with processing results and statistics

        Raises:
            Exception: If processing fails
        """
        # Create root span for entire pipeline execution
        with tracer.start_as_current_span("preprocess_file") as span:
            start_time = time.time()
            file_stats = {
                "input_file": input_path,
                "status": "processing",
                "stages": {},
            }

            filename = Path(input_path).name
            span.set_attribute("file.name", filename)
            span.set_attribute("file.path", input_path)
            logger.info(f"Starting preprocessing pipeline for: {filename}")

            try:
                # Stage 1: Load data
                print(f"  [1/3] Loading: {Path(input_path).name}")
                loaded_data = self.loader.load(input_path)
                file_stats["stages"]["load"] = {
                    "duration": loaded_data["load_time_seconds"],
                    "file_size_mb": loaded_data["file_size_mb"],
                }
                self.metrics["load_duration"].record(loaded_data["load_time_seconds"])
                self.metrics["file_size"].record(loaded_data["file_size_mb"])

                # Stage 2: Process data
                print(f"  [2/3] Processing...")
                processed_data = self.processor.process(loaded_data)
                file_stats["stages"]["process"] = {
                    "duration": processed_data["processing_stats"]["total_processing_time"],
                    "steps": processed_data["processing_stats"]["steps_completed"],
                }
                self.metrics["process_duration"].record(processed_data["processing_stats"]["total_processing_time"])
                # Assuming voxels processed is available in processed_data, otherwise we might need to calculate it
                # For now, let's try to get it from the data shape if possible, or skip if not easily available
                if "data" in processed_data:
                     self.metrics["voxels_processed"].record(processed_data["data"].size)

                # Stage 3: Write output
                print(f"  [3/3] Writing output...")
                if output_filename is None:
                    input_name = Path(input_path).stem
                    if input_name.endswith('.nii'):  # Handle .nii.gz
                        input_name = input_name[:-4]
                    output_filename = f"{input_name}_preprocessed"

                output_path = self.output_dir / output_filename

                write_stats = self.writer.write(
                    processed_data,
                    str(output_path),
                    save_metadata=self.save_metadata,
                    compress=self.compress_output,
                )
                file_stats["stages"]["write"] = {
                    "duration": write_stats["write_time_seconds"],
                    "output_file": write_stats["output_file"],
                    "file_size_kb": write_stats["file_size_kb"],
                }
                self.metrics["write_duration"].record(write_stats["write_time_seconds"])
                
                # Calculate compression ratio if possible (output size / input size)
                # Input size is in MB, output in KB. 
                # input_mb = loaded_data["file_size_mb"]
                # output_mb = write_stats["file_size_kb"] / 1024
                # if input_mb > 0:
                #     ratio = output_mb / input_mb
                #     self.metrics["compression_ratio"].record(ratio)

                # Calculate total time
                total_time = time.time() - start_time
                file_stats["total_duration"] = total_time
                file_stats["status"] = "success"

                # Update span attributes
                span.set_attribute("pipeline.duration", total_time)
                span.set_attribute("pipeline.status", "success")
                span.set_status(trace.Status(trace.StatusCode.OK))

                # Update global statistics
                self.stats["files_processed"] += 1
                self.stats["total_processing_time"] += total_time

                # Record success metrics
                self.metrics["files_processed"].add(1)
                self.metrics["total_duration"].record(total_time)

                print(f"  ✓ Complete in {total_time:.2f}s\n")
                logger.info(f"Pipeline completed successfully for {filename} in {total_time:.2f}s")

                return file_stats

            except Exception as e:
                # Handle errors
                total_time = time.time() - start_time
                file_stats["status"] = "failed"
                file_stats["error"] = str(e)
                file_stats["total_duration"] = total_time

                # Update span with error
                span.set_attribute("pipeline.status", "failed")
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)

                # Update global statistics
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "file": input_path,
                    "error": str(e),
                })

                # Record failure metrics
                self.metrics["files_failed"].add(1)
                self.metrics["processing_errors"].add(1)

                print(f"  ✗ Failed: {e}\n")
                logger.error(f"Pipeline failed for {filename}: {e}")

                raise

    def process_batch(self, input_files: List[str], show_progress: bool = True) -> Dict[str, Any]:
        """
        Process multiple files in batch

        Args:
            input_files: List of input file paths
            show_progress: Show progress bar

        Returns:
            Dictionary with batch processing statistics
        """
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING: {len(input_files)} files")
        print(f"{'='*60}\n")

        batch_start_time = time.time()
        results = []

        # Process each file
        iterator = tqdm(input_files, desc="Processing files") if show_progress else input_files

        for input_file in iterator:
            try:
                result = self.process_file(input_file)
                results.append(result)
            except Exception as e:
                # Continue processing remaining files even if one fails
                results.append({
                    "input_file": input_file,
                    "status": "failed",
                    "error": str(e),
                })

        # Calculate batch statistics
        batch_duration = time.time() - batch_start_time
        successful = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "failed")

        batch_stats = {
            "total_files": len(input_files),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(input_files) * 100,
            "total_duration": batch_duration,
            "average_duration_per_file": batch_duration / len(input_files),
            "results": results,
        }

        # Print summary
        self._print_batch_summary(batch_stats)

        return batch_stats

    def _print_batch_summary(self, batch_stats: Dict[str, Any]) -> None:
        """Print batch processing summary"""
        print(f"\n{'='*60}")
        print("BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total files:     {batch_stats['total_files']}")
        print(f"Successful:      {batch_stats['successful']} "
              f"({batch_stats['success_rate']:.1f}%)")
        print(f"Failed:          {batch_stats['failed']}")
        print(f"Total time:      {batch_stats['total_duration']:.2f}s")
        print(f"Avg per file:    {batch_stats['average_duration_per_file']:.2f}s")
        print(f"{'='*60}\n")

        # Print errors if any
        if self.stats["errors"]:
            print("ERRORS:")
            for error in self.stats["errors"]:
                print(f"  - {error['file']}: {error['error']}")
            print()

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """Reset pipeline statistics"""
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "total_processing_time": 0.0,
            "errors": [],
        }
