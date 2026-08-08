import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///data/swim_analyzer.db"

# connect_args={"check_same_thread": False} is needed only for SQLite.
# If migrating to Postgres, remove connect_args.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Initializes tables and performs schema migrations if needed."""
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    
    # Lightweight SQLite schema migration for coach_id column in athletes table
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("PRAGMA table_info(athletes)"))
            columns = [row[1] for row in result.fetchall()]
            if "coach_id" not in columns:
                conn.execute(text("ALTER TABLE athletes ADD COLUMN coach_id VARCHAR"))
                conn.commit()

            res_coach = conn.execute(text("SELECT coach_id FROM coaches WHERE username = 'coach1'")).fetchone()
            if res_coach:
                c1_id = res_coach[0]
                conn.execute(text("UPDATE athletes SET coach_id = :cid WHERE coach_id IS NULL"), {"cid": c1_id})
                conn.commit()

            # Migration for benchmark_summary_json column in analysis_sessions table
            res_sess = conn.execute(text("PRAGMA table_info(analysis_sessions)"))
            sess_cols = [row[1] for row in res_sess.fetchall()]
            if "benchmark_summary_json" not in sess_cols:
                conn.execute(text("ALTER TABLE analysis_sessions ADD COLUMN benchmark_summary_json TEXT"))
                conn.commit()
    except Exception:
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
