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
    
    # Analysis Settings
    app_config_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "config" / "config.yaml")
    landmark_confidence_threshold: float = 0.5
    
    # Logging
    log_level: str = "INFO"
    debug_mode: bool = False
    
    # VQA Settings
    vqa_blur_threshold: float = 15.0
    vqa_brightness_min: float = 40.0
    vqa_brightness_max: float = 220.0
    vqa_reflection_threshold: float = 0.10
    vqa_early_halt_frames: int = 40
    
    # Video Settings
    video_downscale_width: int = 854
    video_downscale_height: int = 480
    video_default_fps: float = 30.0
    
    # Analysis Constants
    analysis_confidence_penalty: float = 0.20
    calibration_shoulder_width_m: float = 0.40
    
    def __post_init__(self):
        """Ensure all required directories exist and load yaml settings upon initialization."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        if self.app_config_path.exists():
            try:
                import yaml
                with open(self.app_config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                
                log_cfg = data.get("logging", {})
                self.debug_mode = bool(log_cfg.get("debug_mode", self.debug_mode))
                self.log_level = str(log_cfg.get("level", self.log_level))
                
                vqa_cfg = data.get("vqa", {})
                self.vqa_blur_threshold = float(vqa_cfg.get("blur_threshold", self.vqa_blur_threshold))
                self.vqa_brightness_min = float(vqa_cfg.get("brightness_min", self.vqa_brightness_min))
                self.vqa_brightness_max = float(vqa_cfg.get("brightness_max", self.vqa_brightness_max))
                self.vqa_reflection_threshold = float(vqa_cfg.get("reflection_threshold", self.vqa_reflection_threshold))
                self.vqa_early_halt_frames = int(vqa_cfg.get("early_halt_frames", self.vqa_early_halt_frames))
                
                video_cfg = data.get("video", {})
                self.video_downscale_width = int(video_cfg.get("downscale_width", self.video_downscale_width))
                self.video_downscale_height = int(video_cfg.get("downscale_height", self.video_downscale_height))
                
                analysis_cfg = data.get("analysis", {})
                self.video_default_fps = float(analysis_cfg.get("default_fps", self.video_default_fps))
                self.analysis_confidence_penalty = float(analysis_cfg.get("confidence_penalty", self.analysis_confidence_penalty))
                
                calib_cfg = data.get("calibration", {})
                self.calibration_shoulder_width_m = float(calib_cfg.get("shoulder_width_m", self.calibration_shoulder_width_m))
                
            except Exception:
                pass


# Global configuration instance
config = AppConfig()
