"""
Service layer orchestrating the video analysis workflow.
"""
from typing import Tuple, Any
from pathlib import Path

from core.logger import setup_logger
from core.config import config
from utils.video_utils import VideoProcessor
from analysis.pose_detector import PoseDetector
from analysis.calibration_engine import RelativeCalibration
from models.data_models import AnalysisResult, FrameData, JointAngles, VideoMetadata, StrokeDetectionResult, StrokeType
from analysis.strategies.stroke_factory import StrokeStrategyFactory
from services.export_service import ExportService
from datetime import datetime

logger = setup_logger(__name__)

class AnalysisService:
    """
    Orchestrates the workflow of reading a video, running pose detection,
    calculating biomechanics frame by frame, and saving the processed output video.
    """
    
    def __init__(self):
        pass
        
    def _initialize_components(self, effective_fps: float, visualization_mode: str, trajectory_duration_sec: float) -> Tuple[Any, Any, Any]:
        """Initialize detectors and annotators."""
        from analysis.video_quality_assessor import VideoQualityAssessor
        from analysis.video_annotator import VideoAnnotator
        
        vqa = VideoQualityAssessor()
        pose_detector = PoseDetector()
        trajectory_frames = int(effective_fps * trajectory_duration_sec)
        annotator = VideoAnnotator(mode=visualization_mode, trajectory_frames=trajectory_frames)
        
        return vqa, pose_detector, annotator

    def _process_frames_loop(self, processor: VideoProcessor, vqa: Any, pose_detector: Any, annotator: Any, 
                             BiomechanicsCalculator: Any, stroke_analyzer: Any, effective_fps: float, 
                             visualization_mode: str, progress_callback, vqa_callback, analysis_result: AnalysisResult,
                             frame_stride: int = 1) -> Tuple[bool, int, float, float]:
        """Process video frames in a loop, extract poses, calculate biomechanics, and annotate."""
        import time
        import psutil
        import os
        
        last_transition_count = 0
        frames_processed = 0
        valid_frames_count = 0
        raw_frame_counter = 0
        
        process = psutil.Process(os.getpid())
        peak_ram = 0.0
        peak_cpu = 0.0
        
        for frame in processor.generate_frames():
            raw_frame_counter += 1
            # Frame Stride Filtering (e.g. stride 2 = process every 2nd frame)
            if frame_stride > 1 and (raw_frame_counter % frame_stride != 0):
                continue

            current_ram = process.memory_info().rss / (1024 * 1024)
            current_cpu = process.cpu_percent(interval=None)
            if current_ram > peak_ram: peak_ram = current_ram
            if current_cpu > peak_cpu: peak_cpu = current_cpu
            
            # 1. Detect Pose
            landmarks, is_valid = pose_detector.detect_pose(frame)
            if is_valid:
                valid_frames_count += 1
                
            # 2. VQA
            vqa.assess_frame(frame, landmarks, is_valid)
            if frames_processed == config.vqa_early_halt_frames:
                early_vqa = vqa.get_current_result()
                if early_vqa.quality_class == "Critical":
                    logger.warning("VQA returned Critical at early halt check. Halting video processing.")
                    analysis_result.vqa_result = early_vqa
                    if vqa_callback: vqa_callback(early_vqa)
                    return True, valid_frames_count, peak_ram, peak_cpu
                elif vqa_callback:
                    vqa_callback(early_vqa)

            # 3. Biomechanics
            angles = JointAngles()
            stroke_phase = "Unknown"
            phase_conf = 0.0
            timestamp = int(frames_processed * (1000.0 / effective_fps)) if effective_fps > 0 else 0
            
            if landmarks and is_valid:
                angles = BiomechanicsCalculator.calculate_all_angles(landmarks)
                stroke_phase, phase_conf = stroke_analyzer.analyze_frame(landmarks, frames_processed, timestamp)
                
            new_transitions = None
            if len(stroke_analyzer.transitions) > last_transition_count:
                new_transitions = stroke_analyzer.transitions[last_transition_count:]
                last_transition_count = len(stroke_analyzer.transitions)
                
            frame_conf = phase_conf if phase_conf > 0 else (0.95 if is_valid else 0.4)
                
            safe_landmarks = None
            if landmarks:
                safe_landmarks = [
                    type('SimpleLandmark', (), {
                        'x': float(lm.x),
                        'y': float(lm.y),
                        'z': float(getattr(lm, 'z', 0.0)),
                        'visibility': float(getattr(lm, 'visibility', 1.0))
                    })() for lm in landmarks
                ]

            frame_data = FrameData(
                frame_index=frames_processed, timestamp_ms=timestamp, raw_landmarks=safe_landmarks,
                is_valid=is_valid, angles=angles, stroke_phase=stroke_phase, phase_confidence=phase_conf
            )
            analysis_result.frames.append(frame_data)
            
            # 4. Annotate
            annotated_frame = annotator.annotate(
                frame, landmarks, angles, frames_processed, timestamp, 
                frame_conf, stroke_phase, effective_fps, 100.0, 0, new_transitions
            )
            processor.write_frame(annotated_frame)
            
            if progress_callback:
                progress_callback(frame_data, frame_conf, visualization_mode)
            
            frames_processed += 1
            time.sleep(0.001) # Yield GIL
            
        return False, valid_frames_count, peak_ram, peak_cpu

    def _finalize_metrics_and_export(self, analysis_result: AnalysisResult, metadata: VideoMetadata, 
                                     stroke_analyzer: Any, BiomechanicsCalculator: Any, scoring_engine: Any, 
                                     calibration_engine: Any, processor: VideoProcessor, input_filename: str, 
                                     output_video_path: str, athlete_id: Optional[str] = None) -> Tuple[str, str, str]:
        """Finalize metrics, generate reports, run consistency validator, and export JSONs."""
        from models.data_models import StrokeStatistics
        stats = StrokeStatistics(
            time_in_phases=stroke_analyzer.time_in_phases,
            completed_cycles=stroke_analyzer.completed_cycles,
            transitions=stroke_analyzer.transitions
        )
        if stats.completed_cycles > 0:
            stats.average_cycle_duration_ms = (metadata.duration_seconds * 1000) / stats.completed_cycles
            
        valid_phases = [f.phase_confidence for f in analysis_result.frames if f.is_valid and f.stroke_phase != "Unknown"]
        if valid_phases:
            stats.average_phase_confidence = sum(valid_phases) / len(valid_phases)
            
        analysis_result.stroke_statistics = stats
        
        global_metrics = BiomechanicsCalculator.calculate_global_metrics(
            analysis_result.frames, metadata.effective_fps, 
            calibration_engine, processor.width, processor.height
        )
        
        from analysis.reliability_engine import ReliabilityEngine
        analysis_result.reliability = ReliabilityEngine.evaluate(analysis_result)
        
        analysis_result.report = scoring_engine.generate_report(analysis_result, global_metrics)
        
        from analysis.consistency_validator import AnalysisConsistencyValidator
        analysis_result.consistency = AnalysisConsistencyValidator.validate(analysis_result)
        
        # Phase 7: Benchmark Engine Evaluation
        from services.benchmark_service import BenchmarkService
        from services.athlete_service import AthleteService
        athlete_profile = AthleteService().load_profile(athlete_id) if athlete_id else None
        BenchmarkService().evaluate_session(analysis_result, athlete_profile)

        json_report_path, metadata_path, _ = ExportService.export_to_json(analysis_result, metadata, input_filename)
        
        if not VideoProcessor.validate_export(output_video_path):
            logger.error("Video export validation failed. The output video is broken or empty.")
            output_video_path = None
            setattr(analysis_result, 'export_failed', True)
            
        return json_report_path, metadata_path, output_video_path

    def process_video(self, input_video_path: str, effective_fps: float = 30.0,
                      visualization_mode: str = "User Mode", progress_callback=None, vqa_callback=None,
                      trajectory_duration_sec: float = 2.0,
                      stroke_detection: StrokeDetectionResult = None, athlete_id: str = None,
                      frame_stride: int = None) -> Tuple[str, str, str, AnalysisResult]:
        """
        Process a video file to detect poses, calculate angles, and generate an output video.
        """
        stride = frame_stride if frame_stride is not None else config.frame_stride
        stride = max(1, int(stride))
        
        logger.info(f"Starting video processing for: {input_video_path} (Effective FPS: {effective_fps}, Frame Stride: {stride})")
        
        input_filename = Path(input_video_path).name
        output_filename = f"processed_{input_filename}"
        output_video_path = str(config.output_dir / output_filename)
        json_report_path = ""
        metadata_path = ""
        pose_detector = None
        analysis_result = AnalysisResult(video_path=input_video_path)
        
        stroke_type = stroke_detection.selected_stroke if stroke_detection else StrokeType.FREESTYLE
        strategy = StrokeStrategyFactory.get_strategy(stroke_type)
        
        # Adjust effective fps for calculations based on stride
        adjusted_effective_fps = effective_fps / stride if stride > 1 else effective_fps
        stroke_analyzer = strategy.get_stroke_analyzer(adjusted_effective_fps)
        BiomechanicsCalculator = strategy.get_biomechanics_calculator()
        scoring_engine = strategy.get_scoring_engine()
        calibration_engine = RelativeCalibration()
        
        metadata = VideoMetadata(
            filename=input_filename, effective_fps=adjusted_effective_fps, analysis_timestamp=datetime.now().isoformat(),
            swimming_style=stroke_type.value, stroke_detection=stroke_detection,
            calibration_mode=calibration_engine.mode_name, athlete_id=athlete_id
        )
        
        try:
            vqa, pose_detector, annotator = self._initialize_components(adjusted_effective_fps, visualization_mode, trajectory_duration_sec)
            
            with VideoProcessor(input_video_path) as processor:
                if not processor.open(): raise RuntimeError(f"Could not open input video: {input_video_path}")
                
                # Duration Limit Check
                duration_s = processor.frame_count / processor.fps if processor.fps > 0 else 0
                if duration_s > config.max_allowed_duration_s:
                    raise ValueError(f"Video duration ({duration_s:.1f}s) exceeds the maximum allowed limit of {config.max_allowed_duration_s:.0f} seconds. Please upload a shorter clip.")

                if not processor.setup_writer(output_video_path): raise RuntimeError(f"Could not setup output video writer: {output_video_path}")
                    
                metadata.detected_fps = processor.fps
                metadata.resolution_width = processor.width
                metadata.resolution_height = processor.height
                vqa.set_video_metadata(processor.width, processor.height, processor.fps)
                
                import time
                start_time = time.time()
                early_halt, valid_frames_count, peak_ram, peak_cpu = self._process_frames_loop(
                    processor, vqa, pose_detector, annotator, BiomechanicsCalculator, stroke_analyzer,
                    adjusted_effective_fps, visualization_mode, progress_callback, vqa_callback, analysis_result,
                    frame_stride=stride
                )
                
                if early_halt:
                    return "", "", "", analysis_result
                    
                frames_processed = len(analysis_result.frames)
                logger.info(f"Successfully processed {frames_processed} frames.")
                analysis_result.vqa_result = vqa.get_current_result()
                
                processing_time = time.time() - start_time
                metadata.total_frames = frames_processed
                metadata.duration_seconds = frames_processed / effective_fps if effective_fps > 0 else 0
                metadata.processing_time_sec = processing_time
                metadata.peak_ram_mb = peak_ram
                metadata.peak_cpu_percent = peak_cpu
                metadata.average_processing_fps = frames_processed / processing_time if processing_time > 0 else 0
                metadata.confidence_statistics = {
                    "valid_frames": valid_frames_count,
                    "invalid_frames": frames_processed - valid_frames_count,
                    "validity_ratio": valid_frames_count / frames_processed if frames_processed > 0 else 0
                }
                
            json_report_path, metadata_path, output_video_path = self._finalize_metrics_and_export(
                analysis_result, metadata, stroke_analyzer, BiomechanicsCalculator, scoring_engine,
                calibration_engine, processor, input_filename, output_video_path, athlete_id=athlete_id
            )
            
        except Exception as e:
            logger.error(f"Error during video processing: {e}")
            raise e
        finally:
            if pose_detector: pose_detector.close()
                
        return output_video_path, json_report_path, metadata_path, analysis_result
