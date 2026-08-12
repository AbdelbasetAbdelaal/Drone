import hashlib
import os
from datetime import datetime
from typing import List, Optional, Tuple
from database.database import SessionLocal, engine, Base, init_db
from database.repository import CoachRepository
from models.coach_profile import CoachProfile
from core.logger import setup_logger

logger = setup_logger(__name__)

class AuthService:
    """
    Handles secure authentication, password hashing using PBKDF2-HMAC-SHA256,
    and coach registration/multi-tenancy session management.
    """
    
    @staticmethod
    def hash_password(password: str, salt_hex: Optional[str] = None) -> Tuple[str, str]:
        """
        Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
        Returns: (password_hash_hex, salt_hex)
        """
        if salt_hex is None:
            salt_bytes = os.urandom(16)
            salt_hex = salt_bytes.hex()
        else:
            salt_bytes = bytes.fromhex(salt_hex)
            
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt_bytes,
            100000
        )
        return hash_bytes.hex(), salt_hex

    @classmethod
    def register_coach(cls, username: str, password: str, full_name: str, email: str = "", role: str = "coach") -> Tuple[bool, str, Optional[CoachProfile]]:
        """
        Registers a new account.
        Returns: (success: bool, message: str, coach_profile: Optional[CoachProfile])
        """
        username = username.strip().lower()
        role = role.strip().lower() if role else "coach"
        if role not in {"coach", "user", "admin"}:
            return False, "Invalid account role.", None

        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long.", None
            
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        # Ensure database tables exist
        init_db()
        db = SessionLocal()
        try:
            repo = CoachRepository(db)
            existing = repo.get_by_username(username)
            if existing:
                return False, f"Username '{username}' is already taken.", None
                
            pwd_hash, salt = cls.hash_password(password)
            coach = CoachProfile(
                username=username,
                password_hash=pwd_hash,
                salt=salt,
                full_name=full_name.strip() or username,
                role=role,
                email=email.strip() or None,
                created_at=datetime.now().isoformat()
            )
            
            success = repo.add(coach)
            if success:
                logger.info(f"Account registered successfully: {username} ({role})")
                return True, "Account registered successfully!", coach
            else:
                return False, "Failed to save account to database.", None
        finally:
            db.close()

    @classmethod
    def login(cls, username: str, password: str) -> Tuple[bool, str, Optional[CoachProfile]]:
        """
        Authenticates an account.
        Returns: (success: bool, message: str, coach_profile: Optional[CoachProfile])
        """
        username = username.strip().lower()
        init_db()
        db = SessionLocal()
        try:
            repo = CoachRepository(db)
            coach = repo.get_by_username(username)
            if not coach:
                return False, "Invalid username or password.", None
                
            computed_hash, _ = cls.hash_password(password, coach.salt)
            if computed_hash == coach.password_hash:
                logger.info(f"Account logged in: {username} ({coach.role})")
                return True, "Login successful!", coach
            else:
                return False, "Invalid username or password.", None
        finally:
            db.close()

    @classmethod
    def get_all_accounts(cls) -> List[CoachProfile]:
        init_db()
        db = SessionLocal()
        try:
            repo = CoachRepository(db)
            return repo.get_all()
        finally:
            db.close()

    @classmethod
    def delete_account(cls, coach_id: str) -> bool:
        init_db()
        db = SessionLocal()
        try:
            repo = CoachRepository(db)
            return repo.delete(coach_id)
        finally:
            db.close()

    @classmethod
    def seed_default_coach(cls) -> Optional[CoachProfile]:
        """
        Seeds default demo admin and coach accounts if database is empty.
        """
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            repo = CoachRepository(db)
            existing_admin = repo.get_by_username("admin")
            if not existing_admin:
                cls.register_coach("admin", "admin2026", "System Administrator", "admin@swim.ai", role="admin")

            existing = repo.get_by_username("coach1")
            if not existing:
                success, msg, coach = cls.register_coach("coach1", "swim2026", "Coach Alex", "alex@swim.ai", role="coach")
                return coach
            return existing
        except Exception as e:
            logger.warning(f"Error seeding default coach: {e}")
            return None
        finally:
            db.close()
