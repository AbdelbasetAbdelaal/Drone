import pytest
from models.analysis_session import AnalysisSession
from services.analysis_history_service import AnalysisHistoryService
from database.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_analysis_session_serialization():
    session = AnalysisSession(
        athlete_id="user_123",
        analysis_timestamp="2026-08-01T12:00:00.000000",
        original_video_filename="swim_vid.mp4",
        processed_video_filename="processed_swim_vid.mp4",
        metadata_json_path="meta.json",
        report_json_path="report.json",
        performance_score=85.5,
        scientific_confidence="High",
        completed_cycles=12,
        stroke_type="Freestyle",
        processing_time_seconds=45.2
    )

    data = session.to_dict()
    assert data["athlete_id"] == "user_123"
    assert data["performance_score"] == 85.5
    assert "session_id" in data

    loaded_session = AnalysisSession.from_dict(data)
    assert loaded_session.session_id == session.session_id
    assert loaded_session.athlete_id == session.athlete_id
    assert loaded_session.processing_time_seconds == 45.2

def test_analysis_history_service_crud(db_session):
    service = AnalysisHistoryService(db_session=db_session)

    session = AnalysisSession(
        athlete_id="athlete_1",
        analysis_timestamp="2026-08-01T12:00:00.000000",
        original_video_filename="vid1.mp4",
        processed_video_filename="vid1_out.mp4",
        metadata_json_path="meta1.json",
        report_json_path="report1.json",
        performance_score=90.0,
        scientific_confidence="High",
        completed_cycles=10,
        stroke_type="Freestyle",
        processing_time_seconds=30.0
    )

    # Test Save
    assert service.save_session(session) is True

    # Test Load
    loaded = service.load_session(session.session_id)
    assert loaded is not None
    assert loaded.session_id == session.session_id

    # Test Get by Athlete
    sessions = service.get_sessions_by_athlete("athlete_1")
    assert len(sessions) == 1
    assert sessions[0].athlete_id == "athlete_1"

    # Test Delete
    assert service.delete_session(session.session_id) is True
    assert service.load_session(session.session_id) is None

def test_get_sessions_by_athlete_ordering(db_session):
    service = AnalysisHistoryService(db_session=db_session)

    s1 = AnalysisSession(
        athlete_id="athlete_2",
        analysis_timestamp="2026-08-01T10:00:00.000000", # Older
        original_video_filename="old.mp4",
        processed_video_filename="old_out.mp4",
        metadata_json_path="", report_json_path="",
        performance_score=80.0, scientific_confidence="High",
        completed_cycles=5, stroke_type="Freestyle", processing_time_seconds=10.0
    )
    s2 = AnalysisSession(
        athlete_id="athlete_2",
        analysis_timestamp="2026-08-01T12:00:00.000000", # Newer
        original_video_filename="new.mp4",
        processed_video_filename="new_out.mp4",
        metadata_json_path="", report_json_path="",
        performance_score=85.0, scientific_confidence="High",
        completed_cycles=6, stroke_type="Freestyle", processing_time_seconds=12.0
    )

    service.save_session(s1)
    service.save_session(s2)

    sessions = service.get_sessions_by_athlete("athlete_2")
    assert len(sessions) == 2
    # Should be sorted newest first
    assert sessions[0].session_id == s2.session_id
    assert sessions[1].session_id == s1.session_id
