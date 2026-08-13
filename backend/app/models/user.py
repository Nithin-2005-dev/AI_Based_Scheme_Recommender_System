"""
User model with comprehensive profile fields.
Stores all citizen/admin information securely.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text, DateTime,
    ForeignKey, Enum as SAEnum, JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    ADMIN = "admin"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class EmploymentStatus(str, enum.Enum):
    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"
    SELF_EMPLOYED = "self_employed"
    RETIRED = "retired"
    STUDENT = "student"
    HOMEMAKER = "homemaker"


class User(Base):
    """Complete user model with 30+ profile fields."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.CITIZEN.value, nullable=False)

    # ===== Email Verification =====
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(512), nullable=True)

    # ===== Profile Fields =====
    full_name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(30), nullable=True)
    mobile_number = Column(String(15), nullable=True)

    # ===== Occupation & Income =====
    occupation = Column(String(255), nullable=True)
    employment_status = Column(String(50), nullable=True)
    income = Column(Float, nullable=True)  # Monthly income
    annual_family_income = Column(Float, nullable=True)

    # ===== Education =====
    education = Column(String(255), nullable=True)  # e.g., "10th", "12th", "Graduate", "Post-Graduate"

    # ===== Social Category =====
    category = Column(String(50), nullable=True)  # General, OBC, SC, ST
    caste = Column(String(255), nullable=True)
    religion = Column(String(100), nullable=True)
    minority_status = Column(Boolean, default=False)

    # ===== Location =====
    state = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)

    # ===== Special Status =====
    is_disabled = Column(Boolean, default=False)
    disability_type = Column(String(255), nullable=True)
    disability_percentage = Column(Float, nullable=True)
    is_farmer = Column(Boolean, default=False)
    is_student = Column(Boolean, default=False)
    is_widow = Column(Boolean, default=False)
    is_senior_citizen = Column(Boolean, default=False)
    is_pregnant_woman = Column(Boolean, default=False)
    is_business_owner = Column(Boolean, default=False)
    land_ownership = Column(String(100), nullable=True)  # e.g., "No Land", "< 2 Acres", "2-5 Acres", "> 5 Acres"

    # ===== Sensitive Information (AES Encrypted) =====
    aadhaar_encrypted = Column(Text, nullable=True)
    pan_encrypted = Column(Text, nullable=True)

    # ===== Preferences =====
    preferred_languages = Column(JSON, default=["en"])  # List of language codes
    notification_preferences = Column(JSON, default={
        "email": True,
        "sms": False,
        "in_app": True,
    })

    # ===== Profile Completion =====
    profile_completed = Column(Boolean, default=False)
    profile_completion_percentage = Column(Float, default=0.0)

    # ===== Timestamps =====
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    # ===== Relationships =====
    documents = relationship("UserDocument", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    saved_schemes = relationship("SavedScheme", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("ApplicationTracker", back_populates="user", cascade="all, delete-orphan")

    def calculate_profile_completion(self) -> float:
        """Calculate profile completion percentage."""
        fields = [
            self.full_name, self.age, self.gender, self.mobile_number,
            self.occupation, self.employment_status, self.income,
            self.annual_family_income, self.education, self.category,
            self.religion, self.state, self.district, self.pincode,
        ]
        filled = sum(1 for f in fields if f is not None and f != "")
        return round((filled / len(fields)) * 100, 1)


class UserDocument(Base):
    """User-uploaded documents stored securely."""
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(100), nullable=False)  # e.g., "aadhaar", "income_certificate", "caste_certificate"
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_status = Column(String(50), default="pending")  # pending, verified, rejected
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")


class RefreshToken(Base):
    """Refresh tokens for JWT rotation."""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), unique=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="refresh_tokens")
