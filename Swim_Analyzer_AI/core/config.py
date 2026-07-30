"""
Configuration settings for SwimAnalyzer AI.
Using dataclasses to ensure typed and structured configuration.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppConfig:
    """Central configuration for the application."""
    
    # Project Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    input_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "input_videos")
    output_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "output_videos")
    reports_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "reports")
    
    # MediaPipe Settings
    pose_model_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_full.task")
    pose_min_detection_confidence: float = 0.5
    pose_min_tracking_confidence: float = 0.5
    pose_model_complexity: int = 1  # 0, 1, or 2 (higher is more accurate but slower)
    
    # Logging
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Ensure all required directories exist upon initialization."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = AppConfig()
