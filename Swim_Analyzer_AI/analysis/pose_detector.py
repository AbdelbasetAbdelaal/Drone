"""
Pose detection utilizing MediaPipe Tasks API.
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from typing import Optional, Tuple, Any
from core.logger import setup_logger
from core.config import config
from core.constants import COLOR_RED, COLOR_GREEN, COLOR_WHITE, THICKNESS_LANDMARK, THICKNESS_CONNECTION
from models.data_models import JointAngles

logger = setup_logger(__name__)

# Standard 33 landmarks connections for MediaPipe Pose
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
]

class PoseDetector:
    """
    Encapsulates MediaPipe pose estimation logic using the Tasks API.
    Provides methods to detect pose landmarks on an image and draw them.
    """
    
    def __init__(self):
        base_options = python.BaseOptions(model_asset_path=str(config.pose_model_path))
        
        # We process videos frame by frame, so we use VIDEO mode
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=config.pose_min_detection_confidence,
            min_pose_presence_confidence=config.pose_min_tracking_confidence,
            min_tracking_confidence=config.pose_min_tracking_confidence,
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)
        self.frame_timestamp_ms = 0
        logger.info(f"PoseDetector initialized with model: {config.pose_model_path}")
        
    def detect_pose(self, frame: np.ndarray) -> Optional[Any]:
        """
        Process a single BGR frame and detect pose.
        
        Args:
            frame: A numpy array representing a BGR image.
            
        Returns:
            The raw pose landmarks object (or None if not found).
        """
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        detection_result = self.detector.detect_for_video(mp_image, self.frame_timestamp_ms)
        self.frame_timestamp_ms += int(1000 / 30)
        
        if detection_result.pose_landmarks:
            return detection_result.pose_landmarks[0]
        return None
        
    def draw_pose(self, frame: np.ndarray, landmarks: Any, angles: Optional[JointAngles] = None) -> np.ndarray:
        """
        Draw the skeleton and optional angles onto a frame.
        
        Args:
            frame: A numpy array representing a BGR image.
            landmarks: The pose landmarks detected previously.
            angles: Optional JointAngles to display on the frame.
            
        Returns:
            The annotated frame.
        """
        annotated_frame = frame.copy()
        
        if landmarks:
            height, width, _ = annotated_frame.shape
            
            # Map normalized coordinates to pixel coordinates
            pixel_landmarks = []
            for lm in landmarks:
                x = int(lm.x * width)
                y = int(lm.y * height)
                pixel_landmarks.append((x, y))
                
            # Draw connections (bones)
            for connection in POSE_CONNECTIONS:
                start_idx, end_idx = connection
                # Check if we have enough landmarks
                if start_idx < len(pixel_landmarks) and end_idx < len(pixel_landmarks):
                    start_point = pixel_landmarks[start_idx]
                    end_point = pixel_landmarks[end_idx]
                    cv2.line(annotated_frame, start_point, end_point, COLOR_GREEN, THICKNESS_CONNECTION)
            
            # Draw landmarks (joints)
            for x, y in pixel_landmarks:
                cv2.circle(annotated_frame, (x, y), THICKNESS_LANDMARK, COLOR_RED, -1)
                
            # Draw angles if provided
            if angles:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1
                
                # Helper to draw text
                def draw_angle_text(angle_val, landmark_idx):
                    if angle_val is not None and landmark_idx < len(pixel_landmarks):
                        x, y = pixel_landmarks[landmark_idx]
                        text = f"{int(angle_val)}d"
                        cv2.putText(annotated_frame, text, (x + 10, y + 10), font, font_scale, COLOR_WHITE, thickness)
                
                draw_angle_text(angles.left_elbow, 13)
                draw_angle_text(angles.right_elbow, 14)
                draw_angle_text(angles.left_knee, 25)
                draw_angle_text(angles.right_knee, 26)
            
        return annotated_frame
        
    def close(self):
        """Releases the underlying MediaPipe resources."""
        self.detector.close()
        logger.info("PoseDetector resources released.")
