"""
Notification, Deadline, SavedScheme, and ApplicationTracker models.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Notification(Base):
    """In-app, email, and SMS notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # rule_change, deadline, recommendation, system
    channel = Column(String(20), default="in_app")  # in_app, email, sms
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # ===== Related Entity =====
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="SET NULL"), nullable=True)
    scheme_name = Column(String(500), nullable=True)

    # ===== Status =====
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    # ===== Change Details (for rule change notifications) =====
    change_details = Column(JSON, nullable=True)

    # ===== Timestamps =====
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="notifications")


class DeadlineReminder(Base):
    """Scheduled deadline reminders for schemes."""
    __tablename__ = "deadline_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)

    deadline_date = Column(DateTime, nullable=False)
    reminder_days_before = Column(Integer, nullable=False)  # 30, 15, 7, 3, 1, 0
    reminder_type = Column(String(20), default="deadline")  # deadline, renewal

    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SavedScheme(Base):
    """User's saved/bookmarked schemes."""
    __tablename__ = "saved_schemes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)

    notes = Column(Text, nullable=True)
    notify_on_changes = Column(Boolean, default=True)
    saved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="saved_schemes")
    scheme = relationship("Scheme", back_populates="saved_by")


class ApplicationTracker(Base):
    """Track scheme application status."""
    __tablename__ = "application_tracker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(50), default="not_started")  # not_started, documents_pending, submitted, under_review, approved, rejected
    application_date = Column(DateTime, nullable=True)
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    documents_submitted = Column(JSON, default=[])
    missing_documents = Column(JSON, default=[])

    # ===== Eligibility Snapshot =====
    eligibility_status = Column(String(30), nullable=True)  # eligible, partially_eligible, not_eligible
    eligibility_score = Column(Float, nullable=True)
    eligibility_details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="applications")
    scheme = relationship("Scheme", back_populates="applications")


class ChatHistory(Base):
    """RAG chatbot conversation history."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(100), nullable=False, index=True)

    role = Column(String(20), nullable=False)  # user, assistant
    message = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # List of scheme slugs/names cited
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AnalyticsEvent(Base):
    """Track user analytics events."""
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)  # scheme_view, search, recommendation, eligibility_check
    event_data = Column(JSON, nullable=True)
    scheme_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
