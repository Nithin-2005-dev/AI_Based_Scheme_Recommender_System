"""
Scheme model mapped from updated_data.csv.
Stores all government scheme data with versioning for rule change detection.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Table, JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


# Many-to-many association for scheme ↔ tag
scheme_tag_association = Table(
    "scheme_tag_association",
    Base.metadata,
    Column("scheme_id", Integer, ForeignKey("schemes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("scheme_tags.id", ondelete="CASCADE"), primary_key=True),
)


class Scheme(Base):
    """
    Government Scheme model.
    Mapped from CSV columns: scheme_name, slug, details, benefits,
    eligibility, application, documents, level, schemeCategory, tags.
    """
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ===== Core Fields (from CSV) =====
    scheme_name = Column(String(500), nullable=False, index=True)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    details = Column(Text, nullable=True)  # Full description
    benefits = Column(Text, nullable=True)
    eligibility = Column(Text, nullable=True)
    application_process = Column(Text, nullable=True)  # CSV column: "application"
    documents_required = Column(Text, nullable=True)  # CSV column: "documents"
    level = Column(String(20), nullable=False, index=True)  # "Central" or "State"
    scheme_category = Column(String(500), nullable=True, index=True)  # CSV: "schemeCategory"

    # ===== Extended Fields =====
    official_website = Column(String(500), nullable=True)
    application_link = Column(String(500), nullable=True)
    deadline = Column(DateTime, nullable=True)
    renewal_date = Column(DateTime, nullable=True)
    source_pdf_url = Column(String(500), nullable=True)
    language = Column(String(50), default="en")

    # ===== Versioning for Rule Change Detection =====
    version = Column(Integer, default=1)
    rules_json = Column(JSON, nullable=True)  # Structured eligibility rules

    # ===== Metadata =====
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_synced_at = Column(DateTime, nullable=True)

    # ===== NLP-Extracted Fields =====
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    min_income = Column(Float, nullable=True)
    max_income = Column(Float, nullable=True)
    target_gender = Column(String(20), nullable=True)  # "male", "female", "all"
    target_category = Column(String(255), nullable=True)  # "SC", "ST", "OBC", "General", etc.
    target_state = Column(String(100), nullable=True)
    target_occupation = Column(String(255), nullable=True)
    requires_disability = Column(Boolean, default=False)
    requires_farmer = Column(Boolean, default=False)
    requires_student = Column(Boolean, default=False)
    requires_widow = Column(Boolean, default=False)
    requires_senior_citizen = Column(Boolean, default=False)
    requires_pregnant = Column(Boolean, default=False)
    requires_business_owner = Column(Boolean, default=False)

    # ===== Relationships =====
    tags = relationship("SchemeTag", secondary=scheme_tag_association, back_populates="schemes")
    versions = relationship("SchemeVersion", back_populates="scheme", cascade="all, delete-orphan")
    saved_by = relationship("SavedScheme", back_populates="scheme", cascade="all, delete-orphan")
    applications = relationship("ApplicationTracker", back_populates="scheme", cascade="all, delete-orphan")


class SchemeTag(Base):
    """Tags for categorizing and searching schemes."""
    __tablename__ = "scheme_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    schemes = relationship("Scheme", secondary=scheme_tag_association, back_populates="tags")


class SchemeVersion(Base):
    """Version history for rule change detection using Myers Diff."""
    __tablename__ = "scheme_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)

    # ===== Snapshot of scheme at this version =====
    eligibility_snapshot = Column(Text, nullable=True)
    benefits_snapshot = Column(Text, nullable=True)
    documents_snapshot = Column(Text, nullable=True)
    details_snapshot = Column(Text, nullable=True)

    # ===== Change Metadata =====
    change_summary = Column(Text, nullable=True)
    changed_fields = Column(JSON, nullable=True)  # List of field names that changed
    diff_data = Column(JSON, nullable=True)  # Myers diff output

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, nullable=True)  # Admin user ID

    scheme = relationship("Scheme", back_populates="versions")


class SchemeCategory(Base):
    """Normalized scheme categories."""
    __tablename__ = "scheme_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    scheme_count = Column(Integer, default=0)
