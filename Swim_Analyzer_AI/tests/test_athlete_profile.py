import pytest
import tempfile
import os
import shutil
from pathlib import Path
from models.athlete_profile import AthleteProfile
from services.athlete_service import AthleteService

@pytest.fixture
def temp_data_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def athlete_service(temp_data_dir):
    return AthleteService(data_dir=temp_data_dir)

def test_athlete_profile_creation():
    profile = AthleteProfile(
        full_name="John Doe",
        age=25,
        gender="Male",
        height_cm=180.5,
        weight_kg=75.0,
        swimming_level="Advanced",
        preferred_stroke="Freestyle",
        notes="Strong kick"
    )
    
    assert profile.full_name == "John Doe"
    assert profile.athlete_id is not None
    assert type(profile.athlete_id) == str
    assert profile.shoulder_width_cm is None

def test_athlete_profile_serialization():
    profile = AthleteProfile(
        full_name="Jane Smith",
        age=22,
        gender="Female",
        height_cm=165.0,
        weight_kg=60.0,
        swimming_level="Intermediate",
        preferred_stroke="Butterfly",
        shoulder_width_cm=45.0
    )
    
    profile_dict = profile.to_dict()
    assert profile_dict["full_name"] == "Jane Smith"
    assert profile_dict["shoulder_width_cm"] == 45.0
    assert "athlete_id" in profile_dict
    
    loaded_profile = AthleteProfile.from_dict(profile_dict)
    assert loaded_profile.athlete_id == profile.athlete_id
    assert loaded_profile.full_name == "Jane Smith"
    assert loaded_profile.shoulder_width_cm == 45.0
    assert loaded_profile.notes == ""
    assert loaded_profile.schema_version == "1.0"

def test_athlete_service_save_and_load(athlete_service):
    profile = AthleteProfile(
        full_name="Test Swimmer",
        age=30,
        gender="Male",
        height_cm=190.0,
        weight_kg=85.0,
        swimming_level="Elite",
        preferred_stroke="Backstroke"
    )
    
    # Save profile
    success = athlete_service.save_profile(profile)
    assert success is True
    
    # Verify file exists
    file_path = Path(athlete_service.data_dir) / f"{profile.athlete_id}.json"
    assert file_path.exists()
    
    # Load profile
    loaded_profile = athlete_service.load_profile(profile.athlete_id)
    assert loaded_profile is not None
    assert loaded_profile.full_name == "Test Swimmer"
    assert loaded_profile.athlete_id == profile.athlete_id

def test_athlete_service_create(athlete_service):
    profile = athlete_service.create_profile(
        full_name="New Swimmer",
        age=20,
        gender="Female",
        height_cm=170.0,
        weight_kg=65.0,
        swimming_level="Beginner",
        preferred_stroke="Breaststroke"
    )
    assert profile.full_name == "New Swimmer"
    assert profile.athlete_id is not None
    
    # Should be able to load it immediately
    loaded = athlete_service.load_profile(profile.athlete_id)
    assert loaded is not None
    assert loaded.full_name == "New Swimmer"

def test_athlete_service_update_and_delete(athlete_service):
    profile = athlete_service.create_profile(
        full_name="To Update", age=25, gender="Male", height_cm=180, weight_kg=75,
        swimming_level="Advanced", preferred_stroke="Freestyle"
    )
    
    # Update
    profile.full_name = "Updated Name"
    success = athlete_service.update_profile(profile)
    assert success is True
    
    loaded = athlete_service.load_profile(profile.athlete_id)
    assert loaded.full_name == "Updated Name"
    
    # Delete
    success_del = athlete_service.delete_profile(profile.athlete_id)
    assert success_del is True
    
    loaded_deleted = athlete_service.load_profile(profile.athlete_id)
    assert loaded_deleted is None

def test_athlete_service_validation_errors(athlete_service):
    # Invalid profile (missing name, negative age)
    profile = AthleteProfile(
        full_name="",
        age=-5,
        gender="Unknown",
        height_cm=-10.0,
        weight_kg=0,
        swimming_level="",
        preferred_stroke=""
    )
    
    errors = athlete_service.validate_profile(profile)
    assert len(errors) > 0
    
    with pytest.raises(ValueError) as excinfo:
        athlete_service.save_profile(profile)
    assert "Invalid athlete profile" in str(excinfo.value)

def test_athlete_service_get_all_profiles(athlete_service):
    # Create two profiles
    athlete_service.create_profile(
        full_name="Swimmer 1", age=20, gender="Male", height_cm=180, weight_kg=75,
        swimming_level="Beginner", preferred_stroke="Freestyle"
    )
    athlete_service.create_profile(
        full_name="Swimmer 2", age=25, gender="Female", height_cm=170, weight_kg=65,
        swimming_level="Advanced", preferred_stroke="Butterfly"
    )
    
    profiles = athlete_service.get_all_profiles()
    assert len(profiles) == 2
    names = [p.full_name for p in profiles]
    assert "Swimmer 1" in names
    assert "Swimmer 2" in names
