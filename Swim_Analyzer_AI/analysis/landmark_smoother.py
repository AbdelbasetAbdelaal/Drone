"""
Temporal smoothing for pose landmarks to reduce jitter.
"""
import copy
from typing import Any, Optional
from core.logger import setup_logger

logger = setup_logger(__name__)

class LandmarkSmoother:
    """
    Applies Exponential Moving Average (EMA) smoothing to landmark coordinates.
    """
    
    def __init__(self, alpha: float = 0.5):
        """
        Args:
            alpha: Smoothing factor between 0 and 1. 
                   Higher alpha discounts older observations faster.
        """
        self.alpha = alpha
        self.previous_landmarks = None
        
    def smooth(self, current_landmarks: Any) -> Any:
        """
        Applies EMA to the current landmarks based on the previous frame.
        
        Args:
            current_landmarks: Raw landmarks from MediaPipe.
            
        Returns:
            Smoothed landmarks.
        """
        if not current_landmarks:
            self.previous_landmarks = None
            return current_landmarks
            
        # First frame
        if self.previous_landmarks is None:
            self.previous_landmarks = copy.deepcopy(current_landmarks)
            return current_landmarks
            
        smoothed_landmarks = copy.deepcopy(current_landmarks)
        
        try:
            for i in range(len(smoothed_landmarks)):
                prev = self.previous_landmarks[i]
                curr = smoothed_landmarks[i]
                
                # Apply EMA to x, y, z
                curr.x = (self.alpha * curr.x) + ((1 - self.alpha) * prev.x)
                curr.y = (self.alpha * curr.y) + ((1 - self.alpha) * prev.y)
                curr.z = (self.alpha * curr.z) + ((1 - self.alpha) * prev.z)
                
                # We can also smooth visibility/presence if needed, but usually we just keep current
                
            self.previous_landmarks = copy.deepcopy(smoothed_landmarks)
        except Exception as e:
            logger.warning(f"Error during landmark smoothing: {e}")
            return current_landmarks
            
        return smoothed_landmarks
