import pytest
from models.athlete_profile import AthleteProfile
from services.athlete_service import AthleteService
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

def test_athlete_profile_creation():
    profile = AthleteProfile(
        full_name="Michael Phelps",
        age=38,
        gender="Male",
        height_cm=193.0,
        weight_kg=90.0,
        swimming_level="Elite",
        preferred_stroke="Butterfly"
    )
    assert profile.full_name == "Michael Phelps"
    assert profile.athlete_id is not None
    assert len(profile.athlete_id) > 0

def test_athlete_profile_serialization():
    profile = AthleteProfile(
        full_name="Katie Ledecky",
        age=27,
        gender="Female",
        height_cm=183.0,
        weight_kg=73.0,
        swimming_level="Elite",
        preferred_stroke="Freestyle"
    )
    data = profile.to_dict()
    assert data["full_name"] == "Katie Ledecky"
    
    new_profile = AthleteProfile.from_dict(data)
    assert new_profile.athlete_id == profile.athlete_id
    assert new_profile.height_cm == 183.0

def test_athlete_service_save_and_load(db_session):
    service = AthleteService(db_session=db_session)
    profile = AthleteProfile(
        full_name="Ian Thorpe",
        age=41,
        gender="Male",
        height_cm=196.0,
        weight_kg=104.0,
        swimming_level="Elite",
        preferred_stroke="Freestyle"
    )
    
    assert service.save_profile(profile) is True
    loaded_profile = service.load_profile(profile.athlete_id)
    assert loaded_profile is not None
    assert loaded_profile.full_name == "Ian Thorpe"

def test_athlete_service_create(db_session):
    service = AthleteService(db_session=db_session)
    profile = service.create_profile(
        full_name="Sarah Sjostrom",
        age=30,
        gender="Female",
        height_cm=183.0,
        weight_kg=68.0,
        swimming_level="Elite",
        preferred_stroke="Butterfly"
    )
    assert profile.athlete_id is not None
    loaded_profile = service.load_profile(profile.athlete_id)
    assert loaded_profile is not None

def test_athlete_service_update_and_delete(db_session):
    service = AthleteService(db_session=db_session)
    profile = service.create_profile(
        full_name="Adam Peaty",
        age=29,
        gender="Male",
        height_cm=191.0,
        weight_kg=86.0,
        swimming_level="Elite",
        preferred_stroke="Breaststroke"
    )
    
    # Update
    profile.swimming_level = "Professional"
    assert service.update_profile(profile) is True
    loaded = service.load_profile(profile.athlete_id)
    assert loaded.swimming_level == "Professional"
    
    # Delete
    assert service.delete_profile(profile.athlete_id) is True
    assert service.load_profile(profile.athlete_id) is None

def test_athlete_service_validation_errors(db_session):
    service = AthleteService(db_session=db_session)
    profile = AthleteProfile(
        full_name="", # Invalid
        age=-5, # Invalid
        gender="Male",
        height_cm=0, # Invalid
        weight_kg=86.0,
        swimming_level="", # Invalid
        preferred_stroke="Breaststroke"
    )
    
    errors = service.validate_profile(profile)
    assert len(errors) >= 4
    
    with pytest.raises(ValueError):
        service.save_profile(profile)

def test_athlete_service_get_all_profiles(db_session):
    service = AthleteService(db_session=db_session)
    service.create_profile(full_name="A", age=20, gender="M", height_cm=180, weight_kg=80, swimming_level="Pro", preferred_stroke="Free")
    service.create_profile(full_name="B", age=22, gender="F", height_cm=170, weight_kg=60, swimming_level="Amateur", preferred_stroke="Back")
    
    profiles = service.get_all_profiles()
    assert len(profiles) == 2
