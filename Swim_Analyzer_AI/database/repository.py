from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import AthleteModel, AnalysisSessionModel, CoachModel
from models.athlete_profile import AthleteProfile
from models.analysis_session import AnalysisSession
from models.coach_profile import CoachProfile

class CoachRepository:
    """
    Data access repository for Coach entities.
    """
    def __init__(self, db: Session):
        self.db = db

    def add(self, coach: CoachProfile) -> bool:
        db_coach = self.db.query(CoachModel).filter(CoachModel.coach_id == coach.coach_id).first()
        if db_coach:
            for key, value in coach.to_dict().items():
                setattr(db_coach, key, value)
        else:
            valid_keys = {c.name for c in CoachModel.__table__.columns}
            filtered_data = {k: v for k, v in coach.to_dict().items() if k in valid_keys}
            db_coach = CoachModel(**filtered_data)
            self.db.add(db_coach)
            
        try:
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def get_by_id(self, coach_id: str) -> Optional[CoachProfile]:
        db_coach = self.db.query(CoachModel).filter(CoachModel.coach_id == coach_id).first()
        if db_coach:
            data = {c.name: getattr(db_coach, c.name) for c in db_coach.__table__.columns}
            return CoachProfile.from_dict(data)
        return None

    def get_by_username(self, username: str) -> Optional[CoachProfile]:
        db_coach = self.db.query(CoachModel).filter(CoachModel.username == username).first()
        if db_coach:
            data = {c.name: getattr(db_coach, c.name) for c in db_coach.__table__.columns}
            return CoachProfile.from_dict(data)
        return None

    def get_all(self) -> List[CoachProfile]:
        db_coaches = self.db.query(CoachModel).all()
        return [CoachProfile.from_dict({c.name: getattr(coach, c.name) for c in coach.__table__.columns}) for coach in db_coaches]


class AthleteRepository:
    """
    Data access methods (CRUD) for AthleteProfile entities with Coach isolation support.
    """
    def __init__(self, db: Session):
        self.db = db

    def add(self, profile: AthleteProfile) -> bool:
        db_athlete = self.db.query(AthleteModel).filter(AthleteModel.athlete_id == profile.athlete_id).first()
        if db_athlete:
            for key, value in profile.to_dict().items():
                setattr(db_athlete, key, value)
        else:
            valid_keys = {c.name for c in AthleteModel.__table__.columns}
            filtered_data = {k: v for k, v in profile.to_dict().items() if k in valid_keys}
            db_athlete = AthleteModel(**filtered_data)
            self.db.add(db_athlete)
            
        try:
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def get(self, athlete_id: str) -> Optional[AthleteProfile]:
        db_athlete = self.db.query(AthleteModel).filter(AthleteModel.athlete_id == athlete_id).first()
        if db_athlete:
            data = {c.name: getattr(db_athlete, c.name) for c in db_athlete.__table__.columns}
            return AthleteProfile.from_dict(data)
        return None

    def get_all(self, coach_id: Optional[str] = None) -> List[AthleteProfile]:
        query = self.db.query(AthleteModel)
        if coach_id is not None:
            # Strict Multi-tenancy filter: show ONLY athletes owned by this coach
            query = query.filter(AthleteModel.coach_id == coach_id)
            
        db_athletes = query.all()
        profiles = []
        for db_athlete in db_athletes:
            data = {c.name: getattr(db_athlete, c.name) for c in db_athlete.__table__.columns}
            profiles.append(AthleteProfile.from_dict(data))
        return profiles

    def delete(self, athlete_id: str) -> bool:
        db_athlete = self.db.query(AthleteModel).filter(AthleteModel.athlete_id == athlete_id).first()
        if db_athlete:
            try:
                self.db.delete(db_athlete)
                self.db.commit()
                return True
            except Exception:
                self.db.rollback()
                return False
        return False


class AnalysisHistoryRepository:
    """
    Data access methods (CRUD) for AnalysisSession entities.
    """
    def __init__(self, db: Session):
        self.db = db

    def add(self, session: AnalysisSession) -> bool:
        db_session = self.db.query(AnalysisSessionModel).filter(AnalysisSessionModel.session_id == session.session_id).first()
        if db_session:
            for key, value in session.to_dict().items():
                setattr(db_session, key, value)
        else:
            valid_keys = {c.name for c in AnalysisSessionModel.__table__.columns}
            filtered_data = {k: v for k, v in session.to_dict().items() if k in valid_keys}
            db_session = AnalysisSessionModel(**filtered_data)
            self.db.add(db_session)
            
        try:
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def get_by_athlete(self, athlete_id: Optional[str]) -> List[AnalysisSession]:
        db_sessions = self.db.query(AnalysisSessionModel).filter(AnalysisSessionModel.athlete_id == athlete_id).order_by(AnalysisSessionModel.analysis_timestamp.desc()).all()
        sessions = []
        for db_session in db_sessions:
            data = {c.name: getattr(db_session, c.name) for c in db_session.__table__.columns}
            sessions.append(AnalysisSession.from_dict(data))
        return sessions

    def get_all(self) -> List[AnalysisSession]:
        db_sessions = self.db.query(AnalysisSessionModel).order_by(AnalysisSessionModel.analysis_timestamp.desc()).all()
        sessions = []
        for db_session in db_sessions:
            data = {c.name: getattr(db_session, c.name) for c in db_session.__table__.columns}
            sessions.append(AnalysisSession.from_dict(data))
        return sessions

    def get(self, session_id: str) -> Optional[AnalysisSession]:
        db_session = self.db.query(AnalysisSessionModel).filter(AnalysisSessionModel.session_id == session_id).first()
        if db_session:
            data = {c.name: getattr(db_session, c.name) for c in db_session.__table__.columns}
            return AnalysisSession.from_dict(data)
        return None

    def delete(self, session_id: str) -> bool:
        db_session = self.db.query(AnalysisSessionModel).filter(AnalysisSessionModel.session_id == session_id).first()
        if db_session:
            try:
                self.db.delete(db_session)
                self.db.commit()
                return True
            except Exception:
                self.db.rollback()
                return False
        return False
