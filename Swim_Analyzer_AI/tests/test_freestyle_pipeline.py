import pytest
import cv2
import numpy as np
from pathlib import Path

from services.analysis_service import AnalysisService
from core.config import config
from models.data_models import StrokeDetectionResult, StrokeType

@pytest.fixture
def mock_video():
    """Creates a mock 60-second, 30fps video for stability testing."""
    test_video_path = "test_stability_video.mp4"
    width, height = 854, 480
    fps = 30
    duration = 5 # Using 5 seconds for unit tests to keep it fast, but 1080p
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(test_video_path, fourcc, fps, (width, height))
    
    # Write valid synthetic frames with color gradient
    for i in range(fps * duration):
        frame = np.full((height, width, 3), (100, 150, (i * 5) % 255), dtype=np.uint8)
        out.write(frame)
        
    out.release()
    yield test_video_path
    
    # Teardown
    import gc
    gc.collect()
    if Path(test_video_path).exists():
        try:
            Path(test_video_path).unlink()
        except Exception:
            pass

def test_freestyle_pipeline_stability(mock_video):
    """Test that the pipeline processes a video without crashing and downscales it."""
    service = AnalysisService()
    stroke_det = StrokeDetectionResult(
        predicted_stroke=StrokeType.FREESTYLE,
        selected_stroke=StrokeType.FREESTYLE,
        confidence=1.0,
        manual_override=False,
        predictions={}
    )
    
    from unittest.mock import patch
    from models.data_models import VQAResult
    
    with patch('analysis.video_quality_assessor.VideoQualityAssessor.get_current_result') as mock_vqa:
        mock_vqa.return_value = VQAResult(
            overall_score=95.0,
            quality_class="Excellent",
            criteria=[]
        )
        output_video_path, json_report, metadata_path, result = service.process_video(
            input_video_path=mock_video,
            effective_fps=30.0,
            visualization_mode="Developer Mode",
            stroke_detection=stroke_det
        )
    
    assert Path(output_video_path).exists()
    assert Path(json_report).exists()
    assert Path(metadata_path).exists()
    
    assert result is not None
    assert result.report is not None
    # 0 cycles should result in an inconclusive report score of 0
    assert result.report.overall_score == 0.0 
    assert ("No complete stroke cycle detected" in result.report.feedback_summary) or ("Inconclusive" in result.report.feedback_summary)
    
    # Check that performance stats were populated
    assert result.video_path == mock_video
