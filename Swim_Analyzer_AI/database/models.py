from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.database import Base

class AthleteModel(Base):
    __tablename__ = "athletes"

    athlete_id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    shoulder_width_cm = Column(Float, nullable=True)
    swimming_level = Column(String, nullable=False)
    preferred_stroke = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    training_goals = Column(Text, default="")

    analyses = relationship("AnalysisSessionModel", back_populates="athlete", cascade="all, delete-orphan")


class AnalysisSessionModel(Base):
    __tablename__ = "analysis_sessions"

    session_id = Column(String, primary_key=True, index=True)
    athlete_id = Column(String, ForeignKey("athletes.athlete_id"), nullable=True, index=True)
    
    analysis_timestamp = Column(String, nullable=False)
    original_video_filename = Column(String, nullable=False)
    processed_video_filename = Column(String, nullable=False)
    metadata_json_path = Column(String, nullable=False)
    report_json_path = Column(String, nullable=False)
    
    performance_score = Column(Float, nullable=False)
    scientific_confidence = Column(String, nullable=False)
    completed_cycles = Column(Integer, nullable=False)
    stroke_type = Column(String, nullable=False)
    processing_time_seconds = Column(Float, nullable=False)

    athlete = relationship("AthleteModel", back_populates="analyses")
