"""
Service layer orchestrating the video analysis workflow.
"""
from typing import Tuple
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
        
    def process_video(self, input_video_path: str, effective_fps: float, visualization_mode: str = "User Mode", 
                      progress_callback = None, vqa_callback = None, trajectory_duration_sec: float = 2.0,
                      stroke_detection: StrokeDetectionResult = None, athlete_id: str = None) -> Tuple[str, str, str, AnalysisResult]:
        """
        Process a video file to detect poses, calculate angles, and generate an output video.
        
        Args:
            input_video_path (str): The absolute path to the input video.
            effective_fps (float): The framerate to use for time-based calculations.
            visualization_mode (str): One of User Mode, Coach Mode, Developer Mode.
            progress_callback: A function to call per frame with debug data.
            vqa_callback: A function to call with the VQAResult before processing starts.
            trajectory_duration_sec: Length of hand trajectory tail in seconds.
            stroke_detection: StrokeDetectionResult from the pre-analysis phase.
            athlete_id: Optional UUID of the athlete to associate with this analysis.
        """
        logger.info(f"Starting video processing for: {input_video_path} (Effective FPS: {effective_fps})")
        
        input_filename = Path(input_video_path).name
        output_filename = f"processed_{input_filename}"
        output_video_path = str(config.output_dir / output_filename)
        json_report_path = ""
        metadata_path = ""
        
        pose_detector = None
        analysis_result = AnalysisResult(video_path=input_video_path)
        
        stroke_type = stroke_detection.selected_stroke if stroke_detection else StrokeType.FREESTYLE
        strategy = StrokeStrategyFactory.get_strategy(stroke_type)
        stroke_analyzer = strategy.get_stroke_analyzer(effective_fps)
        BiomechanicsCalculator = strategy.get_biomechanics_calculator()
        scoring_engine = strategy.get_scoring_engine()
        
        calibration_engine = RelativeCalibration()
        metadata = VideoMetadata(
            filename=input_filename,
            effective_fps=effective_fps,
            analysis_timestamp=datetime.now().isoformat(),
            swimming_style=stroke_type.value,
            stroke_detection=stroke_detection,
            calibration_mode=calibration_engine.mode_name,
            athlete_id=athlete_id
        )
        
        try:
            # 1. Initialize Video Quality Assessor
            from analysis.video_quality_assessor import VideoQualityAssessor
            vqa = VideoQualityAssessor()
            
            pose_detector = PoseDetector()
            
            # Initialize VideoAnnotator with the requested mode
            from analysis.video_annotator import VideoAnnotator
            trajectory_frames = int(effective_fps * trajectory_duration_sec)
            annotator = VideoAnnotator(mode=visualization_mode, trajectory_frames=trajectory_frames)
            
            with VideoProcessor(input_video_path) as processor:
                if not processor.open():
                    raise RuntimeError(f"Could not open input video: {input_video_path}")
                    
                if not processor.setup_writer(output_video_path):
                    raise RuntimeError(f"Could not setup output video writer: {output_video_path}")
                    
                metadata.detected_fps = processor.fps
                metadata.resolution_width = processor.width
                metadata.resolution_height = processor.height
                
                vqa.set_video_metadata(processor.width, processor.height, processor.fps)
                
                valid_frames_count = 0
                frames_processed = 0
                
                # Keep track of transition count to only pass new ones
                last_transition_count = 0
                
                import time
                import psutil
                import os
                process = psutil.Process(os.getpid())
                start_time = time.time()
                peak_ram = 0.0
                peak_cpu = 0.0
                
                for frame in processor.generate_frames():
                    
                    current_ram = process.memory_info().rss / (1024 * 1024)
                    current_cpu = process.cpu_percent(interval=None)
                    if current_ram > peak_ram: peak_ram = current_ram
                    if current_cpu > peak_cpu: peak_cpu = current_cpu
                    
                    # 1. Detect Pose & Check Confidence (Smoothed)
                    landmarks, is_valid = pose_detector.detect_pose(frame)
                    
                    if is_valid:
                        valid_frames_count += 1
                        
                    # Incremental VQA
                    vqa.assess_frame(frame, landmarks, is_valid)
                    
                    if frames_processed == config.vqa_early_halt_frames:
                        early_vqa = vqa.get_current_result()
                        if early_vqa.quality_class == "Critical":
                            logger.warning("VQA returned Critical at early halt check. Halting video processing.")
                            analysis_result.vqa_result = early_vqa
                            if vqa_callback:
                                vqa_callback(early_vqa)
                            return "", "", "", analysis_result
                        elif vqa_callback:
                            vqa_callback(early_vqa) # Update UI with non-critical early result

                    # 2. Calculate Biomechanics
                    angles = JointAngles()
                    stroke_phase = "Unknown"
                    phase_conf = 0.0
                    timestamp = int(frames_processed * (1000.0 / effective_fps)) if effective_fps > 0 else 0
                    
                    if landmarks and is_valid:
                        angles = BiomechanicsCalculator.calculate_all_angles(landmarks)
                        stroke_phase, phase_conf = stroke_analyzer.analyze_frame(landmarks, frames_processed, timestamp)
                        
                    # Find new transitions
                    new_transitions = None
                    if len(stroke_analyzer.transitions) > last_transition_count:
                        new_transitions = stroke_analyzer.transitions[last_transition_count:]
                        last_transition_count = len(stroke_analyzer.transitions)
                        
                    # Get generic frame confidence
                    frame_conf = phase_conf if phase_conf > 0 else (0.95 if is_valid else 0.4)
                        
                    # 3. Store Data
                    frame_data = FrameData(
                        frame_index=frames_processed,
                        timestamp_ms=timestamp,
                        raw_landmarks=landmarks,
                        is_valid=is_valid,
                        angles=angles,
                        stroke_phase=stroke_phase,
                        phase_confidence=phase_conf
                    )
                    analysis_result.frames.append(frame_data)
                    
                    # 4. Draw and Save
                    annotated_frame = annotator.annotate(
                        frame, landmarks, angles, frames_processed, timestamp, 
                        frame_conf, stroke_phase, effective_fps, 100.0, 0, new_transitions
                    )
                    processor.write_frame(annotated_frame)
                    
                    # 5. Callback for Streamlit Live Update
                    if progress_callback:
                        progress_callback(frame_data, frame_conf, visualization_mode)
                    
                    frames_processed += 1
                    time.sleep(0.001) # Yield GIL so Streamlit websocket doesn't timeout
                    
                logger.info(f"Successfully processed {frames_processed} frames.")
                
                analysis_result.vqa_result = vqa.get_current_result()
                
                metadata.total_frames = frames_processed
                metadata.duration_seconds = frames_processed / effective_fps if effective_fps > 0 else 0
                processing_time = time.time() - start_time
                metadata.processing_time_sec = processing_time
                metadata.peak_ram_mb = peak_ram
                metadata.peak_cpu_percent = peak_cpu
                metadata.average_processing_fps = frames_processed / processing_time if processing_time > 0 else 0
                logger.info(f"Performance - Time: {processing_time:.2f}s, Peak RAM: {peak_ram:.1f}MB, Peak CPU: {peak_cpu:.1f}%")
                metadata.confidence_statistics = {
                    "valid_frames": valid_frames_count,
                    "invalid_frames": frames_processed - valid_frames_count,
                    "validity_ratio": valid_frames_count / frames_processed if frames_processed > 0 else 0
                }
                
            # Attach stroke statistics
            from models.data_models import StrokeStatistics
            stats = StrokeStatistics(
                time_in_phases=stroke_analyzer.time_in_phases,
                completed_cycles=stroke_analyzer.completed_cycles,
                transitions=stroke_analyzer.transitions
            )
            # Calculate average cycle duration
            if stats.completed_cycles > 0:
                stats.average_cycle_duration_ms = (metadata.duration_seconds * 1000) / stats.completed_cycles
                
            # Calculate average phase confidence
            valid_phases = [f.phase_confidence for f in analysis_result.frames if f.is_valid and f.stroke_phase != "Unknown"]
            if valid_phases:
                stats.average_phase_confidence = sum(valid_phases) / len(valid_phases)
                
            analysis_result.stroke_statistics = stats
            
            logger.info("=== Stroke Detection Summary ===")
            logger.info(f"Completed Stroke Cycles: {stats.completed_cycles}")
            logger.info(f"Average Cycle Duration: {stats.average_cycle_duration_ms:.1f}ms")
            logger.info(f"Average Phase Confidence: {stats.average_phase_confidence:.2f}")
            if stats.completed_cycles == 0:
                logger.info("Reason for 0 cycles: The sequence of Recovery -> Entry/Catch/Pull was not observed, likely due to poor visibility, occlusions, or camera angle causing rapid switching between Unknown states.")
            logger.info("=================================")
            
            # Generate Global Metrics & Performance Report
            global_metrics = BiomechanicsCalculator.calculate_global_metrics(
                analysis_result.frames, 
                effective_fps, 
                calibration_engine, 
                processor.width, 
                processor.height
            )
            
            # Calculate Reliability
            from analysis.reliability_engine import ReliabilityEngine
            analysis_result.reliability = ReliabilityEngine.evaluate(analysis_result)
            
            analysis_result.report = scoring_engine.generate_report(analysis_result, global_metrics)
            
            # Final Layer: Consistency Validation
            from analysis.consistency_validator import AnalysisConsistencyValidator
            analysis_result.consistency = AnalysisConsistencyValidator.validate(analysis_result)
            
            logger.info(f"Performance report generated with score: {analysis_result.report.overall_score}")
            
            # Export JSONs
            from services.export_service import ExportService
            json_report_path, metadata_path, timeline_path = ExportService.export_to_json(analysis_result, metadata, input_filename)
            
            # Validate generated video export
            if not VideoProcessor.validate_export(output_video_path):
                logger.error("Video export validation failed. The output video is broken or empty.")
                output_video_path = None
                setattr(analysis_result, 'export_failed', True)
                
        except Exception as e:
            logger.error(f"Error during video processing: {e}")
            raise e
        finally:
            if pose_detector:
                pose_detector.close()
                
        logger.info(f"Finished processing. Output video path: {output_video_path}")
        
        # IMPORTANT: Clear raw_landmarks from all frames before returning.
        # raw_landmarks are MediaPipe C++ extension objects. After pose_detector.close()
        # the C++ backend is freed. If these Python wrapper objects are then stored in
        # st.session_state and the Python GC cleans them up later (after main() returns),
        # it can cause a silent C extension use-after-free crash that kills the entire
        # Streamlit server process without any Python traceback.
        # All downstream consumers of raw_landmarks (scoring, consistency, export) have
        # already run at this point, so it is safe to discard them.
        for frame in analysis_result.frames:
            frame.raw_landmarks = None
        logger.info("raw_landmarks cleared from all frames to prevent C extension GC crash.")
        
        return output_video_path, json_report_path, metadata_path, analysis_result
