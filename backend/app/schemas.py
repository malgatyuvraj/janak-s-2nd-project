"""Pydantic schemas for request/response bodies."""
from datetime import datetime, date, time
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- Job ----------
class JobBase(BaseModel):
    title: str
    department: Optional[str] = ""
    location: Optional[str] = ""
    description: str
    required_skills: str = ""  # comma-separated


class JobCreate(JobBase):
    pass


class JobOut(JobBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Candidate ----------
class CandidateBase(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = ""


class CandidateCreate(CandidateBase):
    pass


class CandidateOut(CandidateBase):
    id: int
    resume_filename: Optional[str] = ""
    skills: str = ""
    experience_years: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------- Application ----------
class ApplicationBase(BaseModel):
    job_id: int
    candidate_id: int
    stage: Optional[str] = "applied"
    notes: Optional[str] = ""


class ApplicationCreate(BaseModel):
    job_id: int
    candidate_id: int
    notes: Optional[str] = ""


class ApplicationUpdate(BaseModel):
    stage: Optional[str] = None
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    stage: str
    match_score: float
    matched_skills: str
    missing_skills: str
    notes: str
    created_at: datetime
    updated_at: datetime
    candidate: Optional[CandidateOut] = None
    job: Optional[JobOut] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Interview ----------
class InterviewBase(BaseModel):
    application_id: int
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = 45
    interviewer: str = ""
    interview_type: str = "video"
    location: str = ""
    notes: str = ""


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    interviewer: Optional[str] = None
    interview_type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InterviewOut(InterviewBase):
    id: int
    status: str
    created_at: datetime
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Pipeline ----------
class PipelineColumn(BaseModel):
    stage: str
    label: str
    applications: List[ApplicationOut]


class PipelineOut(BaseModel):
    job_id: Optional[int] = None
    columns: List[PipelineColumn]
