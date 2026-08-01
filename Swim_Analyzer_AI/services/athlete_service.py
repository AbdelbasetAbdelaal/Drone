import json
import os
from pathlib import Path
from typing import List, Optional
from models.athlete_profile import AthleteProfile
import logging

logger = logging.getLogger(__name__)

class AthleteService:
    def __init__(self, data_dir: str = "data/athletes"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, athlete_id: str) -> Path:
        return self.data_dir / f"{athlete_id}.json"

    def validate_profile(self, profile: AthleteProfile) -> List[str]:
        """Validate athlete profile fields. Returns a list of error messages."""
        errors = []
        if not profile.full_name or not profile.full_name.strip():
            errors.append("Full name is required.")
        if profile.age < 0 or profile.age > 150:
            errors.append("Age must be between 0 and 150.")
        if profile.height_cm <= 0:
            errors.append("Height must be greater than 0.")
        if profile.weight_kg <= 0:
            errors.append("Weight must be greater than 0.")
        if profile.shoulder_width_cm is not None and profile.shoulder_width_cm <= 0:
            errors.append("Shoulder width must be greater than 0 if provided.")
        if not profile.swimming_level:
            errors.append("Swimming level is required.")
        if not profile.preferred_stroke:
            errors.append("Preferred stroke is required.")
        return errors

    def save_profile(self, profile: AthleteProfile) -> bool:
        """Save an athlete profile to a JSON file."""
        errors = self.validate_profile(profile)
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Failed to save athlete profile {profile.athlete_id}: {error_msg}")
            raise ValueError(f"Invalid athlete profile: {error_msg}")
        
        file_path = self._get_file_path(profile.athlete_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=4)
            logger.info(f"Saved athlete profile: {profile.athlete_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving athlete profile {profile.athlete_id}: {e}")
            return False

    def create_profile(self, **kwargs) -> AthleteProfile:
        """Create and save a new athlete profile."""
        profile = AthleteProfile(**kwargs)
        self.save_profile(profile)
        return profile

    def load_profile(self, athlete_id: str) -> Optional[AthleteProfile]:
        """Load an athlete profile from a JSON file."""
        file_path = self._get_file_path(athlete_id)
        if not file_path.exists():
            logger.warning(f"Athlete profile not found: {athlete_id}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AthleteProfile.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading athlete profile {athlete_id}: {e}")
            return None

    def get_all_profiles(self) -> List[AthleteProfile]:
        """Load all athlete profiles in the data directory."""
        profiles = []
        for file_path in self.data_dir.glob("*.json"):
            athlete_id = file_path.stem
            profile = self.load_profile(athlete_id)
            if profile:
                profiles.append(profile)
        return profiles

    def update_profile(self, profile: AthleteProfile) -> bool:
        """Update an existing athlete profile. Alias for save_profile."""
        return self.save_profile(profile)

    def delete_profile(self, athlete_id: str) -> bool:
        """Delete an athlete profile by ID."""
        file_path = self._get_file_path(athlete_id)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted athlete profile: {athlete_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting athlete profile {athlete_id}: {e}")
                return False
        return False

