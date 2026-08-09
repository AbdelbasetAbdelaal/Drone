"""
Unit tests for AIStrokeAgent stroke detection engine.
"""

import pytest
from unittest.mock import MagicMock
from models.data_models import StrokeType
from analysis.classification.ai_stroke_agent import AIStrokeAgent

def _make_mock_frame(lw_y, rw_y, nose_y=0.2, sh_y=0.4, hip_y=0.7):
    lms = [MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9) for _ in range(33)]
    lms[15].y = lw_y # Left wrist
    lms[16].y = rw_y # Right wrist
    lms[11].y = sh_y # Left shoulder
    lms[12].y = sh_y # Right shoulder
    lms[23].y = hip_y # Left hip
    lms[24].y = hip_y # Right hip
    lms[0].y = nose_y # Nose
    return type('SimpleFrame', (), {'raw_landmarks': lms, 'is_valid': True})()

def test_ai_stroke_agent_freestyle_detection():
    """Verify AIStrokeAgent detects Freestyle for alternating arm motion."""
    agent = AIStrokeAgent()
    # Alternating arm trajectory (Left wrist high when Right wrist low)
    frames = [
        _make_mock_frame(0.2, 0.6),
        _make_mock_frame(0.3, 0.5),
        _make_mock_frame(0.4, 0.4),
        _make_mock_frame(0.5, 0.3),
        _make_mock_frame(0.6, 0.2),
        _make_mock_frame(0.5, 0.3),
        _make_mock_frame(0.4, 0.4),
        _make_mock_frame(0.3, 0.5),
    ]

    res = agent.analyze_sequence(frames)
    assert res.predicted_stroke in [StrokeType.FREESTYLE, StrokeType.BACKSTROKE]
    assert res.confidence >= 0.40
    assert "AI Agent Analysis" in res.classification_reason

def test_ai_stroke_agent_butterfly_detection():
    """Verify AIStrokeAgent detects Butterfly for simultaneous arm motion with high recovery."""
    agent = AIStrokeAgent()
    # Simultaneous arm trajectory with overhead recovery (wrist y < shoulder y)
    frames = [
        _make_mock_frame(0.2, 0.2, sh_y=0.4),
        _make_mock_frame(0.3, 0.3, sh_y=0.4),
        _make_mock_frame(0.5, 0.5, sh_y=0.4),
        _make_mock_frame(0.6, 0.6, sh_y=0.4),
        _make_mock_frame(0.4, 0.4, sh_y=0.4),
        _make_mock_frame(0.2, 0.2, sh_y=0.4),
    ]

    res = agent.analyze_sequence(frames)
    assert res.predicted_stroke == StrokeType.BUTTERFLY
    assert res.confidence >= 0.50

def test_ai_stroke_agent_breaststroke_detection():
    """Verify AIStrokeAgent detects Breaststroke for simultaneous underwater arm motion."""
    agent = AIStrokeAgent()
    # Simultaneous arm trajectory underwater below shoulders (wrist y > shoulder y)
    frames = [
        _make_mock_frame(0.45, 0.45, sh_y=0.4),
        _make_mock_frame(0.48, 0.48, sh_y=0.4),
        _make_mock_frame(0.50, 0.50, sh_y=0.4),
        _make_mock_frame(0.48, 0.48, sh_y=0.4),
        _make_mock_frame(0.45, 0.45, sh_y=0.4),
    ]

    res = agent.analyze_sequence(frames)
    assert res.predicted_stroke == StrokeType.BREASTSTROKE
    assert res.confidence >= 0.50

def test_ai_stroke_agent_fallback_empty_frames():
    """Verify AIStrokeAgent handles empty or short frame lists gracefully without fabricated fallbacks."""
    agent = AIStrokeAgent()
    res = agent.analyze_sequence([])
    assert res.predicted_stroke == StrokeType.UNKNOWN
    assert res.confidence is None
    assert res.classification_status == "INSUFFICIENT_EVIDENCE"
