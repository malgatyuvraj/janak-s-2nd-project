"""SQLAlchemy ORM models for the ATS platform."""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    Date,
    Time,
)
from sqlalchemy.orm import relationship

from .database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    department = Column(String(120))
    location = Column(String(120))
    description = Column(Text, nullable=False)
    required_skills = Column(Text, default="")  # comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship(
        "Application", back_populates="job", cascade="all, delete-orphan"
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(64))
    resume_text = Column(Text, default="")  # raw text extracted from upload
    resume_filename = Column(String(255))
    skills = Column(Text, default="")  # comma-separated extracted skills
    experience_years = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship(
        "Application", back_populates="candidate", cascade="all, delete-orphan"
    )


class Application(Base):
    """A candidate's application to a specific job. Holds the AI rank score
    and the pipeline stage used by the kanban board."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    stage = Column(String(40), default="applied", index=True)
    # applied | screening | interview | offer | hired | rejected
    match_score = Column(Float, default=0.0)  # 0..100, AI computed
    matched_skills = Column(Text, default="")  # comma-separated
    missing_skills = Column(Text, default="")  # comma-separated
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    interviews = relationship(
        "Interview", back_populates="application", cascade="all, delete-orphan"
    )


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)
    application_id = Column(
        Integer, ForeignKey("applications.id"), nullable=False
    )
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=45)
    interviewer = Column(String(255), default="")
    interview_type = Column(String(40), default="video")  # video | phone | onsite
    location = Column(String(255), default="")  # meeting link or room
    status = Column(String(20), default="scheduled")  # scheduled | completed | cancelled
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="interviews")
