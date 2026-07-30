"""
Calculates joint angles from pose landmarks.
"""
import numpy as np
from typing import Any
from models.data_models import JointAngles
from core.logger import setup_logger

logger = setup_logger(__name__)

class AngleCalculator:
    """
    Utility class for calculating angles between joints using vector mathematics.
    """
    
    # MediaPipe landmark indices
    L_SHOULDER, L_ELBOW, L_WRIST = 11, 13, 15
    R_SHOULDER, R_ELBOW, R_WRIST = 12, 14, 16
    L_HIP, L_KNEE, L_ANKLE = 23, 25, 27
    R_HIP, R_KNEE, R_ANKLE = 24, 26, 28

    @staticmethod
    def calculate_angle(a: Any, b: Any, c: Any) -> float:
        """
        Calculate the angle between three points.
        Point b is the vertex.
        
        Args:
            a: First point (landmark with x, y).
            b: Vertex point (landmark with x, y).
            c: Third point (landmark with x, y).
            
        Returns:
            float: Angle in degrees between 0 and 180.
        """
        a_coords = np.array([a.x, a.y])
        b_coords = np.array([b.x, b.y])
        c_coords = np.array([c.x, c.y])
        
        radians = np.arctan2(c_coords[1] - b_coords[1], c_coords[0] - b_coords[0]) - \
                  np.arctan2(a_coords[1] - b_coords[1], a_coords[0] - b_coords[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
            
        return angle

    @classmethod
    def calculate_all_angles(cls, landmarks: Any) -> JointAngles:
        """
        Calculate predefined key joint angles from a set of landmarks.
        
        Args:
            landmarks: A list of landmark objects.
            
        Returns:
            JointAngles: Populated dataclass with calculated angles.
        """
        angles = JointAngles()
        
        try:
            if len(landmarks) > max(cls.L_ANKLE, cls.R_ANKLE):
                # Elbows (Shoulder - Elbow - Wrist)
                angles.left_elbow = cls.calculate_angle(
                    landmarks[cls.L_SHOULDER], landmarks[cls.L_ELBOW], landmarks[cls.L_WRIST]
                )
                angles.right_elbow = cls.calculate_angle(
                    landmarks[cls.R_SHOULDER], landmarks[cls.R_ELBOW], landmarks[cls.R_WRIST]
                )
                
                # Knees (Hip - Knee - Ankle)
                angles.left_knee = cls.calculate_angle(
                    landmarks[cls.L_HIP], landmarks[cls.L_KNEE], landmarks[cls.L_ANKLE]
                )
                angles.right_knee = cls.calculate_angle(
                    landmarks[cls.R_HIP], landmarks[cls.R_KNEE], landmarks[cls.R_ANKLE]
                )
        except Exception as e:
            logger.warning(f"Error calculating angles: {e}")
            
        return angles
