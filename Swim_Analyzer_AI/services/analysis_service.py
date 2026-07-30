"""
Service layer orchestrating the video analysis workflow.
"""
from typing import Tuple
from pathlib import Path
from core.logger import setup_logger
from core.config import config
from utils.video_utils import VideoProcessor
from analysis.pose_detector import PoseDetector
from analysis.angle_calculator import AngleCalculator
from analysis.stroke_analyzer import StrokeAnalyzer
from analysis.error_detector import ErrorDetector
from models.data_models import AnalysisResult, FrameData, JointAngles

logger = setup_logger(__name__)

class AnalysisService:
    """
    Orchestrates the workflow of reading a video, running pose detection,
    calculating biomechanics frame by frame, and saving the processed output video.
    """
    
    def __init__(self):
        pass
        
    def process_video(self, input_video_path: str) -> Tuple[str, AnalysisResult]:
        """
        Process a video file to detect poses, calculate angles, and generate an output video.
        
        Args:
            input_video_path (str): The absolute path to the input video.
            
        Returns:
            Tuple[str, AnalysisResult]: 
                - The absolute path to the processed output video.
                - The structured AnalysisResult containing biomechanics data.
            
        Raises:
            Exception: If processing fails at any stage.
        """
        logger.info(f"Starting video processing for: {input_video_path}")
        
        # Prepare output path
        input_filename = Path(input_video_path).name
        output_filename = f"processed_{input_filename}"
        output_video_path = str(config.output_dir / output_filename)
        
        pose_detector = None
        analysis_result = AnalysisResult(video_path=input_video_path)
        stroke_analyzer = StrokeAnalyzer()
        
        try:
            pose_detector = PoseDetector()
            
            with VideoProcessor(input_video_path) as processor:
                if not processor.open():
                    raise RuntimeError(f"Could not open input video: {input_video_path}")
                    
                if not processor.setup_writer(output_video_path):
                    raise RuntimeError(f"Could not setup output video writer: {output_video_path}")
                    
                frames_processed = 0
                for frame in processor.generate_frames():
                    
                    # 1. Detect Pose
                    landmarks = pose_detector.detect_pose(frame)
                    
                    # 2. Calculate Biomechanics
                    angles = None
                    stroke_phase = "Unknown"
                    if landmarks:
                        angles = AngleCalculator.calculate_all_angles(landmarks)
                        stroke_phase = stroke_analyzer.analyze_frame(landmarks)
                        
                    # 3. Store Data
                    timestamp = int(frames_processed * (1000.0 / processor.fps)) if processor.fps > 0 else 0
                    frame_data = FrameData(
                        frame_index=frames_processed,
                        timestamp_ms=timestamp,
                        raw_landmarks=landmarks,
                        angles=angles if angles else JointAngles(),
                        stroke_phase=stroke_phase
                    )
                    analysis_result.frames.append(frame_data)
                    
                    # 4. Draw and Save
                    annotated_frame = pose_detector.draw_pose(frame, landmarks, angles)
                    processor.write_frame(annotated_frame)
                    
                    frames_processed += 1
                    
                logger.info(f"Successfully processed {frames_processed} frames.")
                
            # Generate Performance Report
            error_detector = ErrorDetector()
            analysis_result.report = error_detector.generate_report(analysis_result)
            logger.info(f"Performance report generated with score: {analysis_result.report.overall_score}")
                
        except Exception as e:
            logger.error(f"Error during video processing: {e}")
            raise e
        finally:
            if pose_detector:
                pose_detector.close()
                
        logger.info(f"Finished processing. Output saved to: {output_video_path}")
        return output_video_path, analysis_result
