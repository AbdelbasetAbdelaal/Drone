"""
Domain models for structured data passing across layers.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class StrokeType(str, Enum):
    AUTO_DETECT = "Auto Detect"
    FREESTYLE = "Freestyle"
    BACKSTROKE = "Backstroke"
    BREASTSTROKE = "Breaststroke"
    BUTTERFLY = "Butterfly"
    UNKNOWN = "Unknown"

@dataclass
class StrokeDetectionResult:
    predicted_stroke: StrokeType
    confidence: float
    predictions: Dict[str, float]
    selected_stroke: StrokeType
    manual_override: bool
    is_inconsistent: bool = False

@dataclass
class ValidatedMetric:
    """A generic metric with confidence, reliability, and validation status."""
    value: float = 0.0
    confidence: float = 1.0
    reliability: float = 1.0
    valid: bool = True
    is_estimated: bool = False
    is_insufficient_data: bool = False
    reason_if_invalid: str = ""
    
@dataclass
class JointAngles:
    """Holds calculated angles for key joints in degrees and 3D spatial metrics."""
    left_elbow: Optional[ValidatedMetric] = None
    right_elbow: Optional[ValidatedMetric] = None
    left_knee: Optional[ValidatedMetric] = None
    right_knee: Optional[ValidatedMetric] = None
    left_shoulder: Optional[ValidatedMetric] = None
    right_shoulder: Optional[ValidatedMetric] = None
    left_hip: Optional[ValidatedMetric] = None
    right_hip: Optional[ValidatedMetric] = None
    body_roll: Optional[ValidatedMetric] = None
    # 3D Pose Analytics
    body_roll_3d: Optional[ValidatedMetric] = None
    core_torsion_3d: Optional[ValidatedMetric] = None
    hand_depth_left_3d: Optional[ValidatedMetric] = None
    hand_depth_right_3d: Optional[ValidatedMetric] = None

@dataclass
class VideoMetadata:
    """Stores metadata about the processed video and analysis environment."""
    filename: str = ""
    resolution_width: int = 0
    resolution_height: int = 0
    duration_seconds: float = 0.0
    total_frames: int = 0
    detected_fps: float = 0.0
    effective_fps: float = 0.0
    analysis_timestamp: str = ""
    swimming_style: str = "Freestyle"
    stroke_detection: Optional[StrokeDetectionResult] = None
    processing_time_sec: float = 0.0
    peak_ram_mb: float = 0.0
    peak_cpu_percent: float = 0.0
    average_processing_fps: float = 0.0
    calibration_mode: str = "Unknown"
    confidence_statistics: dict = field(default_factory=dict)
    software_version: str = "1.0.0"
    athlete_id: Optional[str] = None

@dataclass
class VQACriterionResult:
    """Result of a single VQA criterion evaluation."""
    name: str
    score: int
    weight: float
    passed: bool
    explanation_matters: str
    explanation_effect: str
    explanation_fix: str
    
@dataclass
class VQAResult:
    """Stores the complete diagnostic report of the Video Quality Assessment."""
    overall_score: int = 0
    analysis_confidence: str = "High"
    quality_class: str = "Unknown"  # Excellent, Good, Fair, Poor, Critical
    passed: bool = False  # False only if Critical
    warning_message: str = ""
    criteria: List[VQACriterionResult] = field(default_factory=list)
    
@dataclass
class PhaseTransition:
    """Logs a transition between stroke phases."""
    frame_index: int
    timestamp_ms: int
    from_phase: str
    to_phase: str
    reason: str
    confidence: float = 1.0
    
@dataclass
class StrokeStatistics:
    """Statistics about stroke phases across the video."""
    time_in_phases: Dict[str, float] = field(default_factory=lambda: {"Entry": 0.0, "Catch": 0.0, "Pull": 0.0, "Push": 0.0, "Recovery": 0.0, "Unknown": 0.0})
    completed_cycles: int = 0
    average_cycle_duration_ms: float = 0.0
    average_phase_confidence: float = 0.0
    transitions: List[PhaseTransition] = field(default_factory=list)

@dataclass
class FrameData:
    """Represents all analyzed data for a single video frame."""
    frame_index: int
    timestamp_ms: int
    raw_landmarks: Any  # MediaPipe landmarks object or normalized list
    is_valid: bool = True  # Flag if confidence is below threshold
    angles: JointAngles = field(default_factory=JointAngles)
    stroke_phase: str = "Unknown"
    phase_confidence: float = 0.0
    
@dataclass
class MovementError:
    """Represents a specific detected technique flaw."""
    frame_index: int
    timestamp_ms: int
    error_type: str
    description: str
    severity: str  # e.g., 'Low', 'Medium', 'High'
    confidence: float = 1.0
    supporting_metrics: dict = field(default_factory=dict)

@dataclass
class PerformanceReport:
    """Aggregates the overall performance score and all detected errors."""
    overall_score: float = 100.0
    stroke_rate: ValidatedMetric = field(default_factory=ValidatedMetric)
    stroke_length: ValidatedMetric = field(default_factory=ValidatedMetric)
    kick_frequency: ValidatedMetric = field(default_factory=ValidatedMetric)
    stroke_symmetry: ValidatedMetric = field(default_factory=ValidatedMetric)
    errors: List[MovementError] = field(default_factory=list)
    feedback_summary: str = ""

@dataclass
class ReliabilityResult:
    """Contains decoupled scores for Confidence and Reliability."""
    analysis_confidence_score: float = 100.0  # 0-100%
    analysis_confidence_level: str = "High"  # Low, Medium, High
    
    analysis_reliability_score: float = 100.0  # 0-100%
    analysis_reliability_level: str = "High"  # Low, Medium, High
    
    reasons: List[str] = field(default_factory=list)

@dataclass
class ConsistencyReport:
    """Final layer validation to ensure scientific trustworthiness of the report."""
    overall_score: float = 0.0
    validation_status: str = "Inconclusive" # "Passed", "Warning", "Critical", "Inconclusive"
    warnings: List[str] = field(default_factory=list)
    failed_rules: List[str] = field(default_factory=list)
    passed_rules: List[str] = field(default_factory=list)
    scientific_confidence: str = "Inconclusive" # "High", "Medium", "Low", "Inconclusive"

@dataclass
class AnalysisResult:
    """Contains the accumulated analysis across the entire video."""
    video_path: str = ""
    frames: List[FrameData] = field(default_factory=list)
    average_stroke_rate: float = 0.0
    report: Optional[PerformanceReport] = None
    vqa_result: Optional[VQAResult] = None
    stroke_statistics: Optional[StrokeStatistics] = None
    reliability: Optional[ReliabilityResult] = None
    consistency: Optional[ConsistencyReport] = None
    benchmark_result: Optional[Any] = None
    
    def get_angles_timeseries(self) -> Dict[str, List[Optional[float]]]:
        """Returns timeseries data suitable for plotting."""
        return {
            "timestamp_ms": [f.timestamp_ms for f in self.frames],
            "left_elbow": [f.angles.left_elbow.value if f.angles.left_elbow else None for f in self.frames],
            "right_elbow": [f.angles.right_elbow.value if f.angles.right_elbow else None for f in self.frames],
            "left_knee": [f.angles.left_knee.value if f.angles.left_knee else None for f in self.frames],
            "right_knee": [f.angles.right_knee.value if f.angles.right_knee else None for f in self.frames],
        }
