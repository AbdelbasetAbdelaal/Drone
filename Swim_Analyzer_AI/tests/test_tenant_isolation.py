import pytest
import uuid
from database.database import SessionLocal, init_db
from database.repository import AthleteRepository, AnalysisHistoryRepository
from models.athlete_profile import AthleteProfile
from models.analysis_session import AnalysisSession

@pytest.fixture(scope="module")
def setup_db():
    init_db()
    yield

def test_orphaned_athlete_deny_by_default(setup_db):
    db = SessionLocal()
    repo = AthleteRepository(db)
    
    # Create orphaned athlete
    ath_id = str(uuid.uuid4())
    athlete = AthleteProfile(athlete_id=ath_id, full_name="Orphaned Athlete", age=25, gender="Male", height_cm=180, weight_kg=75, swimming_level="Pro", preferred_stroke="Freestyle")
    # By default, coach_id is None
    assert athlete.coach_id is None
    repo.add(athlete)
    
    # Attempt to fetch with a random coach ID should fail
    with pytest.raises(ValueError):
        repo.get(ath_id, None)  # None coach_id must raise ValueError
        
    with pytest.raises(ValueError):
        repo.get(ath_id, "")  # Empty coach_id must raise ValueError
        
    # Attempt to fetch with explicit coach_id should return None (not found)
    assert repo.get(ath_id, "coach_x") is None
    
    db.close()

def test_orphaned_session_deny_by_default(setup_db):
    db = SessionLocal()
    repo = AnalysisHistoryRepository(db)
    
    # Create orphaned session
    sess_id = str(uuid.uuid4())
    session = AnalysisSession(
        session_id=sess_id, athlete_id="ath_x", stroke_type="Freestyle", 
        analysis_timestamp="2026-01-01T00:00:00Z",
        original_video_filename="dummy.mp4",
        processed_video_filename="dummy.mp4",
        metadata_json_path="dummy.json",
        report_json_path="dummy.json",
        performance_score=0.0,
        scientific_confidence="Low",
        completed_cycles=0,
        processing_time_seconds=0.0
    )
    # account_id is None
    assert session.account_id is None
    repo.add(session)
    
    # Attempt to fetch with a random coach ID should fail
    with pytest.raises(ValueError):
        repo.get(sess_id, None)
        
    with pytest.raises(ValueError):
        repo.get(sess_id, "")
        
    # Attempt to fetch with explicit coach_id should return None (not found)
    assert repo.get(sess_id, "coach_x") is None
    
    db.close()
