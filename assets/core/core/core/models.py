"""SQLAlchemy 2.0 Relational Data Models."""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="contributor", nullable=False)
    reputation_score = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    reports = relationship("AccessibilityReport", back_populates="author", cascade="all, delete-orphan")
    confirmations = relationship("ReportConfirmation", back_populates="user", cascade="all, delete-orphan")


class AccessibilityReport(Base):
    __tablename__ = "accessibility_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Integer, default=3, nullable=False)  # 1 (minor) to 5 (impassable)
    status = Column(String(20), default="unverified", nullable=False, index=True)  # unverified, verified, disputed, resolved
    trust_score = Column(Float, default=0.5, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    author = relationship("User", back_populates="reports")
    confirmations = relationship("ReportConfirmation", back_populates="report", cascade="all, delete-orphan")
    disputes = relationship("ReportDispute", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_reports_coords", "latitude", "longitude"),
        Index("idx_reports_cat_status", "category", "status"),
    )


class ReportConfirmation(Base):
    __tablename__ = "report_confirmations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("accessibility_reports.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    report = relationship("AccessibilityReport", back_populates="confirmations")
    user = relationship("User", back_populates="confirmations")

    __table_args__ = (
        Index("idx_unique_user_report_confirm", "report_id", "user_id", unique=True),
    )


class ReportDispute(Base):
    __tablename__ = "report_disputes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("accessibility_reports.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    report = relationship("AccessibilityReport", back_populates="disputes")


class Place(Base):
    __tablename__ = "places"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # hospital, college, transit, park, etc.
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=True)
    
    # Accessibility Flags
    step_free_access = Column(Boolean, default=False, nullable=False)
    elevator_available = Column(Boolean, default=False, nullable=False)
    tactile_paving = Column(Boolean, default=False, nullable=False)
    accessible_restroom = Column(Boolean, default=False, nullable=False)
    accessible_parking = Column(Boolean, default=False, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    last_verified_at = Column(DateTime, nullable=True)
