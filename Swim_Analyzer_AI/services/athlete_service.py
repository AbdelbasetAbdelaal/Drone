from typing import List, Optional
from models.athlete_profile import AthleteProfile
from database import SessionLocal, AthleteRepository
import logging

logger = logging.getLogger(__name__)

class AthleteService:
    def __init__(self, db_session=None):
        self._owns_session = False
        if db_session is None:
            self.db = SessionLocal()
            self._owns_session = True
        else:
            self.db = db_session
        self.repository = AthleteRepository(self.db)

    def __del__(self):
        if hasattr(self, '_owns_session') and self._owns_session and self.db:
            try:
                self.db.close()
            except Exception:
                pass

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
        """Save an athlete profile to the database."""
        errors = self.validate_profile(profile)
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Failed to save athlete profile {profile.athlete_id}: {error_msg}")
            raise ValueError(f"Invalid athlete profile: {error_msg}")
        
        success = self.repository.add(profile)
        if success:
            logger.info(f"Saved athlete profile: {profile.athlete_id}")
        else:
            logger.error(f"Error saving athlete profile {profile.athlete_id} to database.")
        return success

    def create_profile(self, **kwargs) -> AthleteProfile:
        """Create and save a new athlete profile."""
        profile = AthleteProfile(**kwargs)
        self.save_profile(profile)
        return profile

    def load_profile(self, athlete_id: str) -> Optional[AthleteProfile]:
        """Load an athlete profile from the database."""
        profile = self.repository.get(athlete_id)
        if not profile:
            logger.warning(f"Athlete profile not found: {athlete_id}")
        return profile

    def get_all_profiles(self, coach_id: Optional[str] = None) -> List[AthleteProfile]:
        """Load all athlete profiles for the given coach from the database."""
        return self.repository.get_all(coach_id=coach_id)

    def update_profile(self, profile: AthleteProfile) -> bool:
        """Update an existing athlete profile. Alias for save_profile."""
        return self.save_profile(profile)

    def delete_profile(self, athlete_id: str) -> bool:
        """Delete an athlete profile by ID."""
        success = self.repository.delete(athlete_id)
        if success:
            logger.info(f"Deleted athlete profile: {athlete_id}")
        else:
            logger.error(f"Error deleting athlete profile {athlete_id}")
        return success
