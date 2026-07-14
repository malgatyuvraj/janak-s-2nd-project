# AI-Powered Recruitment & ATS Platform

An Applicant Tracking System with AI-based candidate screening.
Built with **React.js**, **Python (NLP)**, **FastAPI**, and **PostgreSQL**.

## Features

Exactly the four features in the spec — nothing extra:

1. **Resume parsing & ranking** — Upload a PDF, DOCX or TXT resume. The system
   extracts skills, experience, and produces an AI match score per job.
2. **Skill matching with job descriptions** — Each application is auto-scored
   against the job's required skills and full description using TF-IDF +
   cosine similarity combined with skill-overlap analysis.
3. **Hiring pipeline visualization** — Kanban board with the six standard
   stages (Applied → Screening → Interview → Offer → Hired → Rejected).
   Drag-and-drop is implemented as a stage selector on each card.
4. **Interview scheduling** — Schedule, reschedule, complete, or cancel
   interviews. Scheduling an interview auto-advances the candidate's
   pipeline stage.

## Tech Stack

- **Frontend**: React 18 + Vite. Single-page app, no extra UI library.
- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic 2.
- **NLP**: pure Python + numpy (TF-IDF + cosine similarity implemented
  inline so the project runs on Python 3.13 / 3.14 without compiled
  wheels). PDF via `PyPDF2`, DOCX via `python-docx`.
- **Database**: PostgreSQL.

## Layout

```
backend/
  app/
    database.py     # SQLAlchemy engine/session
    models.py       # ORM models
    schemas.py      # Pydantic request/response schemas
    nlp.py          # resume parser + TF-IDF skill matcher
    main.py         # FastAPI endpoints
  test_api.py       # end-to-end backend test (54 assertions)
  test_file_parsing.py  # PDF + DOCX resume parsing test
frontend/
  src/
    App.jsx         # top-level shell + tabs
    api.js          # fetch wrapper
    styles.css      # single stylesheet
    components/
      Dashboard.jsx
      Jobs.jsx
      Candidates.jsx
      Pipeline.jsx     # kanban
      Interviews.jsx
```

## Running locally

### Prerequisites

- Python 3.13+ (project was developed against 3.13)
- Node 20+
- PostgreSQL running on `localhost:5432`

### 1. Create the database

```bash
createdb ats_platform
```

If your Postgres needs credentials, set `DATABASE_URL`:

```bash
export DATABASE_URL='postgresql://USER:PASS@localhost:5432/ats_platform'
```

### 2. Backend

```bash
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Tables are created automatically on startup. API docs are at
<http://127.0.0.1:8000/docs>.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173/>. The Vite dev server proxies `/api/*`
to the FastAPI backend.

## API Endpoints

### Jobs
- `POST /api/jobs` — create
- `GET /api/jobs` — list
- `GET /api/jobs/{id}` — read
- `DELETE /api/jobs/{id}` — delete

### Candidates
- `POST /api/candidates` — create (no resume)
- `GET /api/candidates` — list
- `GET /api/candidates/{id}` — read
- `POST /api/candidates/upload` — **upload a resume (PDF/DOCX/TXT)**;
  parses skills + experience on the server

### Applications & skill matching
- `POST /api/applications` — apply a candidate to a job (computes match score)
- `GET /api/applications` — list (optionally `?job_id=N`)
- `GET /api/applications/{id}` — read
- `GET /api/applications/{id}/match` — recompute match breakdown
- `PATCH /api/applications/{id}/stage?stage=X` — move stage
- `DELETE /api/applications/{id}` — remove
- `GET /api/jobs/{id}/ranked-candidates` — **ranked list for a job**

### Pipeline
- `GET /api/pipeline` — all columns (optionally `?job_id=N`)

### Interviews
- `POST /api/interviews` — schedule
- `GET /api/interviews` — list (optionally `?application_id=N`)
- `GET /api/interviews/{id}` — read
- `PATCH /api/interviews/{id}` — update / reschedule / mark complete
- `DELETE /api/interviews/{id}` — cancel

## NLP Scoring

For each application, the score (0..100) is computed as:

```
final = 0.4 * tfidf_cosine + 0.6 * skill_overlap_pct
```

- `tfidf_cosine` — TF-IDF + cosine similarity between resume text and
  job description (with English stop-word removal)
- `skill_overlap_pct` — `%` of the job's required skills that the
  candidate's resume contains

If a job has no explicit required-skills list, the system extracts
skills from the description text and uses those instead.

## Tests

Two end-to-end test scripts live in `backend/`:

```bash
cd backend
source venv/bin/activate
python test_api.py             # 54 assertions, all features
python test_file_parsing.py    # PDF + DOCX parsing
```

Both pass on a fresh database.
