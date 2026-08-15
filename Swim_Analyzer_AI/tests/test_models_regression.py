import pytest
from models.athlete_profile import AthleteProfile
from models.analysis_session import AnalysisSession

def test_athlete_profile_requires_coach_id():
    with pytest.raises(TypeError) as excinfo:
        AthleteProfile(full_name="Test", age=20, gender="Male", height_cm=180, weight_kg=80, swimming_level="Pro", preferred_stroke="Free")
    assert "coach_id" in str(excinfo.value)

def test_analysis_session_requires_account_id():
    with pytest.raises(TypeError) as excinfo:
        AnalysisSession(
            athlete_id="user_123",
            analysis_timestamp="2026-08-01T12:00:00",
            original_video_filename="a.mp4",
            processed_video_filename="b.mp4",
            metadata_json_path="c.json",
            report_json_path="d.json",
            performance_score=80.0,
            scientific_confidence="High",
            completed_cycles=1,
            stroke_type="Freestyle",
            processing_time_seconds=10.0
        )
    assert "account_id" in str(excinfo.value)
