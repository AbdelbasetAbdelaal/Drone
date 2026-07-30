"""
Analyzes stroke phases based on motion tracking over time.
"""
from typing import Any
from core.logger import setup_logger

logger = setup_logger(__name__)

class StrokeAnalyzer:
    """
    Maintains state across frames to detect swimming stroke phases.
    This implementation uses a generic heuristic tracking the wrist's 
    Y-coordinate relative to the shoulder.
    """
    
    L_SHOULDER, L_WRIST = 11, 15
    R_SHOULDER, R_WRIST = 12, 16

    def __init__(self):
        self.current_phase = "Unknown"
        # We can store history here if we need temporal smoothing
        self.wrist_y_history = []
        
    def analyze_frame(self, landmarks: Any) -> str:
        """
        Determine the stroke phase for the current frame.
        
        Args:
            landmarks: A list of landmark objects.
            
        Returns:
            str: The detected phase (e.g., "Recovery", "Pull", "Catch").
        """
        if not landmarks or len(landmarks) <= max(self.L_WRIST, self.R_WRIST):
            return self.current_phase
            
        try:
            # We'll use the right arm for this generic example
            r_shoulder = landmarks[self.R_SHOULDER]
            r_wrist = landmarks[self.R_WRIST]
            
            # Y-axis is inverted in image coordinates (0 is top)
            # If wrist is physically higher (smaller Y) than shoulder by a margin -> Recovery
            if r_wrist.y < r_shoulder.y - 0.05:
                new_phase = "Recovery"
            # If wrist is significantly lower -> Pull
            elif r_wrist.y > r_shoulder.y + 0.1:
                new_phase = "Pull"
            else:
                new_phase = "Catch / Glide"
                
            self.current_phase = new_phase
            
        except Exception as e:
            logger.warning(f"Error during stroke analysis: {e}")
            
        return self.current_phase
