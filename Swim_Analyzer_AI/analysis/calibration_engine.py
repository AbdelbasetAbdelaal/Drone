"""
Calibration engines for converting pixel measurements into physical or relative measurements.
"""
from abc import ABC, abstractmethod
from typing import Any
import numpy as np

class CalibrationEngine(ABC):
    """
    Abstract base class for measurement calibration.
    """
    @property
    @abstractmethod
    def mode_name(self) -> str:
        pass

    @abstractmethod
    def calibrate_distance(self, p1: Any, p2: Any, frame_width: int, frame_height: int, reference_landmarks: Any = None) -> float:
        """
        Converts pixel distance between two points into a calibrated measurement.
        
        Args:
            p1: First point (normalized x,y)
            p2: Second point (normalized x,y)
            frame_width: Video width
            frame_height: Video height
            reference_landmarks: The full list of landmarks for the frame (used for relative calibration)
            
        Returns:
            The calibrated distance as a float.
        """
        pass

class RelativeCalibration(CalibrationEngine):
    """
    Normalizes distance based on the swimmer's estimated body height in the frame.
    Returns measurements in "Body Lengths".
    """
    
    @property
    def mode_name(self) -> str:
        return "Relative (Body Height)"

    def calibrate_distance(self, p1: Any, p2: Any, frame_width: int, frame_height: int, reference_landmarks: Any = None) -> float:
        if not reference_landmarks or len(reference_landmarks) < 29:
            return 0.0
            
        # Calculate raw pixel distance between p1 and p2
        pixel_dist = np.sqrt(
            ((p1.x - p2.x) * frame_width)**2 + 
            ((p1.y - p2.y) * frame_height)**2
        )
        
        # Estimate body height using Shoulder to Ankle distance (average of left/right)
        l_shoulder, r_shoulder = reference_landmarks[11], reference_landmarks[12]
        l_ankle, r_ankle = reference_landmarks[27], reference_landmarks[28]
        
        shoulder_mid_x = (l_shoulder.x + r_shoulder.x) / 2
        shoulder_mid_y = (l_shoulder.y + r_shoulder.y) / 2
        ankle_mid_x = (l_ankle.x + r_ankle.x) / 2
        ankle_mid_y = (l_ankle.y + r_ankle.y) / 2
        
        body_height_pixels = np.sqrt(
            ((shoulder_mid_x - ankle_mid_x) * frame_width)**2 + 
            ((shoulder_mid_y - ankle_mid_y) * frame_height)**2
        )
        
        if body_height_pixels <= 0:
            return 0.0
            
        return float(pixel_dist / body_height_pixels)
