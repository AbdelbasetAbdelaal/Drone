import logging
from typing import List, Optional
from models.analysis_session import AnalysisSession
from database import SessionLocal, AnalysisHistoryRepository

logger = logging.getLogger(__name__)

class AnalysisHistoryService:
    def __init__(self, db_session=None):
        self._owns_session = False
        if db_session is None:
            self.db = SessionLocal()
            self._owns_session = True
        else:
            self.db = db_session
        self.repository = AnalysisHistoryRepository(self.db)

    def __del__(self):
        if hasattr(self, '_owns_session') and self._owns_session and self.db:
            try:
                self.db.close()
            except Exception:
                pass

    def save_session(self, session: AnalysisSession) -> bool:
        """Save an analysis session to the database."""
        success = self.repository.add(session)
        if success:
            logger.info(f"Saved analysis session: {session.session_id}")
        else:
            logger.error(f"Error saving analysis session {session.session_id} to database.")
        return success

    def load_session(self, session_id: str) -> Optional[AnalysisSession]:
        """Load an analysis session from the database."""
        session = self.repository.get(session_id)
        if not session:
            logger.warning(f"Analysis session not found: {session_id}")
        return session

    def get_sessions_by_athlete(self, athlete_id: Optional[str]) -> List[AnalysisSession]:
        """Load all analysis sessions for a specific athlete (or None for guest)."""
        return self.repository.get_by_athlete(athlete_id)

    def get_all_sessions(self) -> List[AnalysisSession]:
        """Load all analysis sessions across all athletes."""
        return self.repository.get_all()

    def delete_session(self, session_id: str) -> bool:
        """Delete an analysis session by ID."""
        success = self.repository.delete(session_id)
        if success:
            logger.info(f"Deleted analysis session: {session_id}")
        else:
            logger.error(f"Error deleting analysis session {session_id}")
        return success
