"""
Domain models for structured data passing across layers.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class JointAngles:
    """Holds calculated angles for key joints in degrees."""
    left_elbow: Optional[float] = None
    right_elbow: Optional[float] = None
    left_knee: Optional[float] = None
    right_knee: Optional[float] = None

@dataclass
class FrameData:
    """Represents all analyzed data for a single video frame."""
    frame_index: int
    timestamp_ms: int
    raw_landmarks: Any  # MediaPipe landmarks object or normalized list
    angles: JointAngles = field(default_factory=JointAngles)
    stroke_phase: str = "Unknown"
    
@dataclass
class MovementError:
    """Represents a specific detected technique flaw."""
    frame_index: int
    timestamp_ms: int
    error_type: str
    description: str
    severity: str  # e.g., 'Low', 'Medium', 'High'

@dataclass
class PerformanceReport:
    """Aggregates the overall performance score and all detected errors."""
    overall_score: float = 100.0
    errors: List[MovementError] = field(default_factory=list)
    feedback_summary: str = ""

@dataclass
class AnalysisResult:
    """Contains the accumulated analysis across the entire video."""
    video_path: str = ""
    frames: List[FrameData] = field(default_factory=list)
    average_stroke_rate: float = 0.0
    report: Optional[PerformanceReport] = None
    
    def get_angles_timeseries(self) -> Dict[str, List[Optional[float]]]:
        """Returns timeseries data suitable for plotting."""
        return {
            "timestamp_ms": [f.timestamp_ms for f in self.frames],
            "left_elbow": [f.angles.left_elbow for f in self.frames],
            "right_elbow": [f.angles.right_elbow for f in self.frames],
            "left_knee": [f.angles.left_knee for f in self.frames],
            "right_knee": [f.angles.right_knee for f in self.frames],
        }
