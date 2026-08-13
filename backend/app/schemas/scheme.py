"""
Pydantic schemas for schemes, recommendations, eligibility, search, notifications, chatbot, analytics.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ===== Scheme Schemas =====
class SchemeResponse(BaseModel):
    id: int
    scheme_name: str
    slug: str
    details: Optional[str] = None
    benefits: Optional[str] = None
    eligibility: Optional[str] = None
    application_process: Optional[str] = None
    documents_required: Optional[str] = None
    level: str
    scheme_category: Optional[str] = None
    tags: list[str] = []
    official_website: Optional[str] = None
    application_link: Optional[str] = None
    deadline: Optional[datetime] = None
    is_active: bool = True
    view_count: int = 0
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SchemeListResponse(BaseModel):
    schemes: list[SchemeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SchemeCreateRequest(BaseModel):
    scheme_name: str = Field(..., max_length=500)
    slug: str = Field(..., max_length=300)
    details: Optional[str] = None
    benefits: Optional[str] = None
    eligibility: Optional[str] = None
    application_process: Optional[str] = None
    documents_required: Optional[str] = None
    level: str = Field(..., pattern="^(Central|State)$")
    scheme_category: Optional[str] = None
    tags: list[str] = []
    official_website: Optional[str] = None
    application_link: Optional[str] = None
    deadline: Optional[datetime] = None


class SchemeUpdateRequest(BaseModel):
    scheme_name: Optional[str] = None
    details: Optional[str] = None
    benefits: Optional[str] = None
    eligibility: Optional[str] = None
    application_process: Optional[str] = None
    documents_required: Optional[str] = None
    level: Optional[str] = None
    scheme_category: Optional[str] = None
    tags: Optional[list[str]] = None
    official_website: Optional[str] = None
    application_link: Optional[str] = None
    deadline: Optional[datetime] = None
    is_active: Optional[bool] = None


# ===== Recommendation Schemas =====
class RecommendationResponse(BaseModel):
    scheme: SchemeResponse
    score: float
    confidence: float
    reasons: list[str]
    matched_conditions: list[str]
    failed_conditions: list[str]
    eligibility_probability: float


class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationResponse]
    total_evaluated: int
    user_profile_summary: dict


# ===== Eligibility Schemas =====
class EligibilityCheckRequest(BaseModel):
    scheme_id: int


class EligibilityResult(BaseModel):
    scheme_id: int
    scheme_name: str
    status: str  # eligible, partially_eligible, not_eligible
    score: float
    confidence: float
    matched_criteria: list[str]
    failed_criteria: list[str]
    missing_documents: list[str]
    suggestions: list[str]
    explanation: str


# ===== Search Schemas =====
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = None
    level: Optional[str] = None
    state: Optional[str] = None
    tags: Optional[list[str]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)


class SearchResponse(BaseModel):
    results: list[SchemeResponse]
    total: int
    page: int
    page_size: int
    query: str
    suggestions: list[str] = []


# ===== Notification Schemas =====
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    channel: str
    priority: str
    scheme_name: Optional[str] = None
    is_read: bool
    change_details: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class SendNotificationRequest(BaseModel):
    """Admin-triggered notification."""
    title: str
    message: str
    notification_type: str = "system"
    target_users: Optional[list[int]] = None  # None = all users
    scheme_id: Optional[int] = None
    priority: str = "normal"


# ===== Chatbot Schemas =====
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    language: str = "en"


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict]  # [{"scheme_name": str, "slug": str, "relevance": float}]
    confidence: float
    session_id: str
    source_chunks: list[str] = []
    language: str = "en"


# ===== Analytics Schemas =====
class DashboardStats(BaseModel):
    total_users: int
    total_schemes: int
    total_central: int
    total_state: int
    total_categories: int
    total_notifications_sent: int
    total_applications: int
    active_users_today: int


class CategoryStats(BaseModel):
    category: str
    count: int
    percentage: float


class StateStats(BaseModel):
    state: str
    user_count: int
    scheme_count: int


class PopularScheme(BaseModel):
    scheme_name: str
    slug: str
    view_count: int
    application_count: int
    category: Optional[str] = None


class AnalyticsDashboard(BaseModel):
    stats: DashboardStats
    popular_schemes: list[PopularScheme]
    category_distribution: list[CategoryStats]
    state_usage: list[StateStats]
    eligibility_distribution: dict
    monthly_signups: list[dict]
    notification_stats: dict


# ===== Translation Schemas =====
class TranslateRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    source_language: str = "en"
    target_language: str


class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 1.0


# ===== Saved Scheme =====
class SaveSchemeRequest(BaseModel):
    scheme_id: int
    notes: Optional[str] = None
    notify_on_changes: bool = True


class SavedSchemeResponse(BaseModel):
    id: int
    scheme: SchemeResponse
    notes: Optional[str] = None
    notify_on_changes: bool
    saved_at: datetime

    model_config = {"from_attributes": True}


# ===== Application Tracker =====
class ApplicationUpdateRequest(BaseModel):
    status: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    documents_submitted: Optional[list[str]] = None


class ApplicationResponse(BaseModel):
    id: int
    scheme_id: int
    scheme_name: str
    status: str
    application_date: Optional[datetime] = None
    reference_number: Optional[str] = None
    eligibility_status: Optional[str] = None
    eligibility_score: Optional[float] = None
    missing_documents: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
