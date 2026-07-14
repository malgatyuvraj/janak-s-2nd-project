"""FastAPI application — AI-Powered Recruitment & ATS Platform.

Endpoints cover exactly the four features requested:

  1. Resume parsing & ranking
     POST /api/candidates/upload           upload + parse a resume
     GET  /api/jobs/{id}/ranked-candidates ranked list for a job

  2. Skill matching with job descriptions
     POST /api/applications                apply candidate to job (computes match)
     POST /api/jobs/{id}/apply/{cid}       same as above via path
     GET  /api/applications/{id}/match     recompute match details

  3. Hiring pipeline visualization
     GET    /api/pipeline                  all columns (applied/screening/...)
     GET    /api/pipeline?job_id=N         pipeline for one job
     PATCH  /api/applications/{id}/stage   move candidate between stages

  4. Interview scheduling
     POST   /api/interviews                schedule an interview
     GET    /api/interviews                list interviews (filter by app_id/date)
     PATCH  /api/interviews/{id}           reschedule / update
     DELETE /api/interviews/{id}           cancel

Plus basic CRUD for jobs and candidates so the frontend has something to talk to.
"""
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from . import models, schemas, nlp
from .database import engine, Base, get_db

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="AI-Powered Recruitment & ATS Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "ok", "app": "AI-Powered Recruitment & ATS Platform"}


# ===========================================================================
# Jobs
# ===========================================================================
@app.post("/api/jobs", response_model=schemas.JobOut)
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    obj = models.Job(**job.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/api/jobs", response_model=List[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(models.Job).order_by(desc(models.Job.created_at)).all()


@app.get("/api/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Job, job_id)
    if not obj:
        raise HTTPException(404, "Job not found")
    return obj


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Job, job_id)
    if not obj:
        raise HTTPException(404, "Job not found")
    db.delete(obj)
    db.commit()
    return {"deleted": True}


# ===========================================================================
# Candidates  (also covers feature 1: resume parsing on upload)
# ===========================================================================
@app.post("/api/candidates", response_model=schemas.CandidateOut)
def create_candidate(cand: schemas.CandidateCreate, db: Session = Depends(get_db)):
    if db.query(models.Candidate).filter_by(email=cand.email).first():
        raise HTTPException(400, "Candidate with this email already exists")
    obj = models.Candidate(**cand.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/api/candidates", response_model=List[schemas.CandidateOut])
def list_candidates(db: Session = Depends(get_db)):
    return (
        db.query(models.Candidate)
        .order_by(desc(models.Candidate.created_at))
        .all()
    )


@app.get("/api/candidates/{cid}", response_model=schemas.CandidateOut)
def get_candidate(cid: int, db: Session = Depends(get_db)):
    obj = db.get(models.Candidate, cid)
    if not obj:
        raise HTTPException(404, "Candidate not found")
    return obj


@app.post("/api/candidates/upload", response_model=schemas.CandidateOut)
def upload_resume(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a resume (PDF/DOCX/TXT). The resume is parsed, skills and
    experience are extracted, and a candidate row is created (or updated if
    the email already exists)."""
    content = file.file.read()
    if not content:
        raise HTTPException(400, "Empty file")

    parsed = nlp.parse_resume(file.filename or "", content)

    # save a copy on disk so re-processing is possible
    safe_name = f"{email.replace('@', '_at_')}_{file.filename or 'resume'}"
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    try:
        with open(save_path, "wb") as fh:
            fh.write(content)
    except Exception:
        save_path = ""

    cand = db.query(models.Candidate).filter_by(email=email).first()
    if cand:
        cand.full_name = full_name
        cand.phone = phone or cand.phone
        cand.resume_text = parsed["resume_text"]
        cand.resume_filename = safe_name
        cand.skills = ", ".join(parsed["skills"])
        cand.experience_years = parsed["experience_years"]
    else:
        cand = models.Candidate(
            full_name=full_name,
            email=email,
            phone=phone,
            resume_text=parsed["resume_text"],
            resume_filename=safe_name,
            skills=", ".join(parsed["skills"]),
            experience_years=parsed["experience_years"],
        )
        db.add(cand)
    db.commit()
    db.refresh(cand)
    return cand


# ===========================================================================
# Applications  (covers feature 2: skill matching)
# ===========================================================================
VALID_STAGES = ["applied", "screening", "interview", "offer", "hired", "rejected"]


def _split_skills(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _build_application_response(db: Session, app_row: models.Application) -> schemas.ApplicationOut:
    return schemas.ApplicationOut(
        id=app_row.id,
        job_id=app_row.job_id,
        candidate_id=app_row.candidate_id,
        stage=app_row.stage,
        match_score=app_row.match_score,
        matched_skills=app_row.matched_skills,
        missing_skills=app_row.missing_skills,
        notes=app_row.notes,
        created_at=app_row.created_at,
        updated_at=app_row.updated_at,
        candidate=schemas.CandidateOut.model_validate(app_row.candidate) if app_row.candidate else None,
        job=schemas.JobOut.model_validate(app_row.job) if app_row.job else None,
    )


@app.post("/api/applications", response_model=schemas.ApplicationOut)
def create_application(
    payload: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
):
    """Apply a candidate to a job — computes skill match on the spot."""
    job = db.get(models.Job, payload.job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    cand = db.get(models.Candidate, payload.candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")

    existing = (
        db.query(models.Application)
        .filter_by(job_id=job.id, candidate_id=cand.id)
        .first()
    )
    if existing:
        # re-score instead of duplicating
        _rescore(existing, job, cand)
        if payload.notes is not None:
            existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return _build_application_response(db, existing)

    app_row = models.Application(
        job_id=job.id,
        candidate_id=cand.id,
        notes=payload.notes or "",
        stage="applied",
    )
    db.add(app_row)
    db.flush()  # assign id so relationships load
    _rescore(app_row, job, cand)
    db.commit()
    db.refresh(app_row)
    return _build_application_response(db, app_row)


def _rescore(app_row: models.Application,
             job: Optional[models.Job] = None,
             cand: Optional[models.Candidate] = None) -> None:
    if job is None:
        job = app_row.job
    if cand is None:
        cand = app_row.candidate
    if not job or not cand:
        return
    required = _split_skills(job.required_skills)
    cand_skills = _split_skills(cand.skills)
    match = nlp.compute_match(
        job.description or "",
        required,
        cand.resume_text or "",
        cand_skills,
    )
    app_row.match_score = match["score"]
    app_row.matched_skills = ", ".join(match["matched_skills"])
    app_row.missing_skills = ", ".join(match["missing_skills"])


@app.get("/api/applications", response_model=List[schemas.ApplicationOut])
def list_applications(
    job_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Application)
    if job_id is not None:
        q = q.filter_by(job_id=job_id)
    rows = q.order_by(desc(models.Application.match_score)).all()
    return [_build_application_response(db, r) for r in rows]


@app.get("/api/applications/{app_id}", response_model=schemas.ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Application, app_id)
    if not row:
        raise HTTPException(404, "Application not found")
    return _build_application_response(db, row)


@app.get("/api/applications/{app_id}/match")
def get_match(app_id: int, db: Session = Depends(get_db)):
    """Recompute and return the full match breakdown for an application."""
    row = db.get(models.Application, app_id)
    if not row:
        raise HTTPException(404, "Application not found")
    job = row.job or db.get(models.Job, row.job_id)
    cand = row.candidate or db.get(models.Candidate, row.candidate_id)
    _rescore(row, job, cand)
    db.commit()
    return {
        "score": row.match_score,
        "matched_skills": _split_skills(row.matched_skills),
        "missing_skills": _split_skills(row.missing_skills),
    }


@app.patch("/api/applications/{app_id}/stage")
def move_stage(
    app_id: int,
    stage: str = Query(...),
    db: Session = Depends(get_db),
):
    """Move a candidate between pipeline stages."""
    if stage not in VALID_STAGES:
        raise HTTPException(400, f"Invalid stage. Allowed: {VALID_STAGES}")
    row = db.get(models.Application, app_id)
    if not row:
        raise HTTPException(404, "Application not found")
    row.stage = stage
    db.commit()
    db.refresh(row)
    return _build_application_response(db, row)


@app.delete("/api/applications/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Application, app_id)
    if not row:
        raise HTTPException(404, "Application not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


# ===========================================================================
# Feature 1 (cont.) — Ranked candidates for a job
# ===========================================================================
@app.get("/api/jobs/{job_id}/ranked-candidates")
def ranked_candidates(job_id: int, db: Session = Depends(get_db)):
    """Return candidates for a job, ordered by AI match score."""
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    required = _split_skills(job.required_skills)
    apps = (
        db.query(models.Application)
        .filter_by(job_id=job_id)
        .all()
    )
    out = []
    for a in apps:
        out.append({
            "application_id": a.id,
            "candidate_id": a.candidate_id,
            "candidate_name": a.candidate.full_name if a.candidate else "",
            "candidate_email": a.candidate.email if a.candidate else "",
            "candidate_skills": _split_skills(a.candidate.skills) if a.candidate else [],
            "experience_years": a.candidate.experience_years if a.candidate else 0,
            "match_score": a.match_score,
            "matched_skills": _split_skills(a.matched_skills),
            "missing_skills": _split_skills(a.missing_skills),
            "stage": a.stage,
        })
    out.sort(key=lambda x: x["match_score"], reverse=True)
    return {"job_id": job_id, "job_title": job.title, "results": out}


# ===========================================================================
# Feature 3 — Hiring pipeline (kanban)
# ===========================================================================
STAGE_LABELS = {
    "applied": "Applied",
    "screening": "Screening",
    "interview": "Interview",
    "offer": "Offer",
    "hired": "Hired",
    "rejected": "Rejected",
}


@app.get("/api/pipeline", response_model=schemas.PipelineOut)
def pipeline(job_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Return the kanban board as ordered columns. Optionally scoped to one job."""
    q = db.query(models.Application)
    if job_id is not None:
        q = q.filter_by(job_id=job_id)
    rows = q.order_by(desc(models.Application.match_score)).all()
    cols = {s: [] for s in VALID_STAGES}
    for r in rows:
        if r.stage not in cols:
            cols[r.stage] = []
        cols[r.stage].append(_build_application_response(db, r))
    columns = [
        schemas.PipelineColumn(stage=s, label=STAGE_LABELS[s], applications=cols[s])
        for s in VALID_STAGES
    ]
    return schemas.PipelineOut(job_id=job_id, columns=columns)


# ===========================================================================
# Feature 4 — Interview scheduling
# ===========================================================================
@app.post("/api/interviews", response_model=schemas.InterviewOut)
def schedule_interview(payload: schemas.InterviewCreate, db: Session = Depends(get_db)):
    app_row = db.get(models.Application, payload.application_id)
    if not app_row:
        raise HTTPException(404, "Application not found")
    obj = models.Interview(**payload.model_dump())
    obj.status = "scheduled"
    db.add(obj)
    # auto-advance stage to interview
    if app_row.stage in ("applied", "screening"):
        app_row.stage = "interview"
    db.commit()
    db.refresh(obj)
    return _interview_to_out(obj)


@app.get("/api/interviews", response_model=List[schemas.InterviewOut])
def list_interviews(
    application_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Interview)
    if application_id is not None:
        q = q.filter_by(application_id=application_id)
    rows = q.order_by(models.Interview.scheduled_date, models.Interview.scheduled_time).all()
    return [_interview_to_out(r) for r in rows]


@app.get("/api/interviews/{iid}", response_model=schemas.InterviewOut)
def get_interview(iid: int, db: Session = Depends(get_db)):
    obj = db.get(models.Interview, iid)
    if not obj:
        raise HTTPException(404, "Interview not found")
    return _interview_to_out(obj)


@app.patch("/api/interviews/{iid}", response_model=schemas.InterviewOut)
def update_interview(
    iid: int,
    payload: schemas.InterviewUpdate,
    db: Session = Depends(get_db),
):
    obj = db.get(models.Interview, iid)
    if not obj:
        raise HTTPException(404, "Interview not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return _interview_to_out(obj)


@app.delete("/api/interviews/{iid}")
def cancel_interview(iid: int, db: Session = Depends(get_db)):
    obj = db.get(models.Interview, iid)
    if not obj:
        raise HTTPException(404, "Interview not found")
    obj.status = "cancelled"
    db.commit()
    return {"cancelled": True, "id": iid}


def _interview_to_out(obj: models.Interview) -> schemas.InterviewOut:
    cand_name = None
    job_title = None
    if obj.application and obj.application.candidate:
        cand_name = obj.application.candidate.full_name
    if obj.application and obj.application.job:
        job_title = obj.application.job.title
    return schemas.InterviewOut(
        id=obj.id,
        application_id=obj.application_id,
        scheduled_date=obj.scheduled_date,
        scheduled_time=obj.scheduled_time,
        duration_minutes=obj.duration_minutes,
        interviewer=obj.interviewer,
        interview_type=obj.interview_type,
        location=obj.location,
        status=obj.status,
        notes=obj.notes,
        created_at=obj.created_at,
        candidate_name=cand_name,
        job_title=job_title,
    )
