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

    def load_session(self, session_id: str, account_id: Optional[str] = None) -> Optional[AnalysisSession]:
        """Load an analysis session from the database, enforcing account ownership if provided."""
        session = self.repository.get(session_id)
        if not session:
            logger.warning(f"Analysis session not found: {session_id}")
            return None
            
        if account_id is not None and session.account_id:
            if str(session.account_id) != str(account_id):
                logger.warning(f"Security: Unauthorized access attempt to session {session_id} by account {account_id}")
                return None
                
        return session

    def get_sessions_by_athlete(self, athlete_id: Optional[str]) -> List[AnalysisSession]:
        """Load all analysis sessions for a specific athlete (or None for guest)."""
        return self.repository.get_by_athlete(athlete_id)

    def get_sessions_by_account(self, account_id: str) -> List[AnalysisSession]:
        """Load all analysis sessions for a specific account."""
        return self.repository.get_by_account(account_id)

    def get_all_sessions(self) -> List[AnalysisSession]:
        """Load all analysis sessions across all athletes."""
        return self.repository.get_all()

    def get_performance_history_df(self, athlete_id: Optional[str] = None):
        """Returns a Pandas DataFrame of performance progression for historical charting."""
        import pandas as pd
        sessions = self.get_sessions_by_athlete(athlete_id) if athlete_id else self.get_all_sessions()
        rows = []
        for s in sessions:
            dt_parts = s.analysis_timestamp.split("T")
            date_str = dt_parts[0]
            time_str = dt_parts[1][:5] if len(dt_parts) > 1 else "00:00"
            rows.append({
                "SessionID": s.session_id,
                "AthleteID": s.athlete_id,
                "Date": date_str,
                "Time": time_str,
                "Score": s.performance_score,
                "Confidence": s.scientific_confidence,
                "Cycles": s.completed_cycles,
                "Stroke": s.stroke_type
            })
        return pd.DataFrame(rows)

    def delete_session(self, session_id: str, account_id: Optional[str] = None) -> bool:
        """Delete an analysis session by ID, enforcing account ownership if provided."""
        session = self.load_session(session_id, account_id=account_id)
        if not session:
            logger.warning(f"Security/Not Found: Cannot delete session {session_id}")
            return False
            
        success = self.repository.delete(session_id)
        if success:
            logger.info(f"Deleted analysis session: {session_id}")
        else:
            logger.error(f"Error deleting analysis session {session_id}")
        return success


