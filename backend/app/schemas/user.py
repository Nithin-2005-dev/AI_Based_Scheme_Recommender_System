"""
Pydantic schemas for user profile management.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserProfileUpdate(BaseModel):
    """Update user profile with all 30+ fields."""
    full_name: Optional[str] = Field(None, max_length=255)
    age: Optional[int] = Field(None, ge=0, le=300)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    mobile_number: Optional[str] = Field(None, max_length=15)

    # Occupation & Income
    occupation: Optional[str] = None
    employment_status: Optional[str] = None
    income: Optional[float] = Field(None, ge=0)
    annual_family_income: Optional[float] = Field(None, ge=0)

    # Education
    education: Optional[str] = None

    # Social Category
    category: Optional[str] = None
    caste: Optional[str] = None
    religion: Optional[str] = None
    minority_status: Optional[bool] = None

    # Location
    state: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = Field(None, max_length=10)

    # Special Status
    is_disabled: Optional[bool] = None
    disability_type: Optional[str] = None
    disability_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_farmer: Optional[bool] = None
    is_student: Optional[bool] = None
    is_widow: Optional[bool] = None
    is_senior_citizen: Optional[bool] = None
    is_pregnant_woman: Optional[bool] = None
    is_business_owner: Optional[bool] = None
    land_ownership: Optional[str] = None

    # Sensitive (will be encrypted)
    aadhaar: Optional[str] = None
    pan: Optional[str] = None

    # Preferences
    preferred_languages: Optional[list[str]] = None
    notification_preferences: Optional[dict] = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    mobile_number: Optional[str] = None

    occupation: Optional[str] = None
    employment_status: Optional[str] = None
    income: Optional[float] = None
    annual_family_income: Optional[float] = None
    education: Optional[str] = None

    category: Optional[str] = None
    caste: Optional[str] = None
    religion: Optional[str] = None
    minority_status: bool = False

    state: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None

    is_disabled: bool = False
    disability_type: Optional[str] = None
    is_farmer: bool = False
    is_student: bool = False
    is_widow: bool = False
    is_senior_citizen: bool = False
    is_pregnant_woman: bool = False
    is_business_owner: bool = False
    land_ownership: Optional[str] = None

    has_aadhaar: bool = False
    has_pan: bool = False

    preferred_languages: list[str] = ["en"]
    notification_preferences: dict = {}

    profile_completed: bool = False
    profile_completion_percentage: float = 0.0

    role: str = "citizen"
    is_email_verified: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    id: int
    document_type: str
    document_name: str
    file_size: Optional[int] = None
    is_verified: bool = False
    verification_status: str = "pending"
    uploaded_at: datetime

    model_config = {"from_attributes": True}
