from database.database import Base, engine, get_db, SessionLocal
from database.models import AthleteModel, AnalysisSessionModel
from database.repository import AthleteRepository, AnalysisHistoryRepository

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(bind=engine)
