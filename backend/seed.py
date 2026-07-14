import os
import random
from datetime import datetime, timedelta, time

# Set up paths and imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app import models

def get_random_date():
    today = datetime.now().date()
    return today + timedelta(days=random.randint(1, 14))

def get_random_time():
    hour = random.randint(9, 16)
    minute = random.choice([0, 15, 30, 45])
    return time(hour, minute)

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create Jobs
    jobs_data = [
        {"title": "Senior Frontend Engineer", "department": "Engineering", "location": "Remote", "description": "Looking for a React expert to build beautiful UIs.", "required_skills": "React, TypeScript, CSS, HTML"},
        {"title": "Backend Python Developer", "department": "Engineering", "location": "New York, NY", "description": "FastAPI and PostgreSQL experience required.", "required_skills": "Python, FastAPI, SQL, Docker"},
        {"title": "Product Designer", "department": "Design", "location": "San Francisco, CA", "description": "Create amazing user experiences and UI designs.", "required_skills": "Figma, UI/UX, CSS, Prototyping"},
        {"title": "DevOps Engineer", "department": "Infrastructure", "location": "Remote", "description": "Manage our cloud infrastructure and CI/CD pipelines.", "required_skills": "AWS, Kubernetes, Terraform, CI/CD"}
    ]

    jobs = []
    for jd in jobs_data:
        j = models.Job(**jd)
        db.add(j)
        jobs.append(j)
    
    db.commit()
    for j in jobs:
        db.refresh(j)

    # Create Candidates
    candidates_data = [
        {"full_name": "Alice Smith", "email": "alice@example.com", "phone": "555-0101", "skills": "React, CSS, HTML, JavaScript", "experience_years": 4},
        {"full_name": "Bob Johnson", "email": "bob@example.com", "phone": "555-0102", "skills": "Python, Django, SQL", "experience_years": 3},
        {"full_name": "Charlie Davis", "email": "charlie@example.com", "phone": "555-0103", "skills": "Figma, Sketch, UI/UX, CSS", "experience_years": 6},
        {"full_name": "Diana Prince", "email": "diana@example.com", "phone": "555-0104", "skills": "AWS, Docker, Linux, Terraform", "experience_years": 5},
        {"full_name": "Evan Wright", "email": "evan@example.com", "phone": "555-0105", "skills": "React, TypeScript, Node.js, Next.js", "experience_years": 7},
        {"full_name": "Fiona Gallagher", "email": "fiona@example.com", "phone": "555-0106", "skills": "Python, FastAPI, Docker, Kubernetes", "experience_years": 2},
        {"full_name": "George Miller", "email": "george@example.com", "phone": "555-0107", "skills": "Figma, Adobe XD, HTML, CSS", "experience_years": 1},
        {"full_name": "Hannah Abbott", "email": "hannah@example.com", "phone": "555-0108", "skills": "Java, Spring, SQL, AWS", "experience_years": 8},
        {"full_name": "Ian Malcolm", "email": "ian@example.com", "phone": "555-0109", "skills": "React, Python, SQL", "experience_years": 4},
        {"full_name": "Julia Roberts", "email": "julia@example.com", "phone": "555-0110", "skills": "Terraform, Ansible, AWS, Kubernetes", "experience_years": 6}
    ]

    candidates = []
    for cd in candidates_data:
        c = models.Candidate(**cd)
        db.add(c)
        candidates.append(c)
    
    db.commit()
    for c in candidates:
        db.refresh(c)

    # Create Applications
    applications_data = [
        # Job 1: Frontend (React, TypeScript, CSS, HTML)
        {"job": jobs[0], "candidate": candidates[0], "match_score": 85.0, "matched_skills": "React, CSS, HTML", "missing_skills": "TypeScript", "stage": "interview"},
        {"job": jobs[0], "candidate": candidates[4], "match_score": 95.0, "matched_skills": "React, TypeScript, CSS, HTML", "missing_skills": "", "stage": "offer"},
        {"job": jobs[0], "candidate": candidates[8], "match_score": 60.0, "matched_skills": "React", "missing_skills": "TypeScript, CSS, HTML", "stage": "rejected"},

        # Job 2: Backend (Python, FastAPI, SQL, Docker)
        {"job": jobs[1], "candidate": candidates[1], "match_score": 75.0, "matched_skills": "Python, SQL", "missing_skills": "FastAPI, Docker", "stage": "screening"},
        {"job": jobs[1], "candidate": candidates[5], "match_score": 90.0, "matched_skills": "Python, FastAPI, Docker", "missing_skills": "SQL", "stage": "interview"},
        
        # Job 3: Design (Figma, UI/UX, CSS, Prototyping)
        {"job": jobs[2], "candidate": candidates[2], "match_score": 85.0, "matched_skills": "Figma, UI/UX, CSS", "missing_skills": "Prototyping", "stage": "hired"},
        {"job": jobs[2], "candidate": candidates[6], "match_score": 65.0, "matched_skills": "Figma, CSS", "missing_skills": "UI/UX, Prototyping", "stage": "applied"},

        # Job 4: DevOps (AWS, Kubernetes, Terraform, CI/CD)
        {"job": jobs[3], "candidate": candidates[3], "match_score": 80.0, "matched_skills": "AWS, Terraform", "missing_skills": "Kubernetes, CI/CD", "stage": "interview"},
        {"job": jobs[3], "candidate": candidates[9], "match_score": 90.0, "matched_skills": "AWS, Kubernetes, Terraform", "missing_skills": "CI/CD", "stage": "offer"},
    ]

    applications = []
    for ad in applications_data:
        app = models.Application(
            job_id=ad["job"].id,
            candidate_id=ad["candidate"].id,
            match_score=ad["match_score"],
            matched_skills=ad["matched_skills"],
            missing_skills=ad["missing_skills"],
            stage=ad["stage"]
        )
        db.add(app)
        applications.append(app)

    db.commit()
    for a in applications:
        db.refresh(a)

    # Create Interviews
    interviews_data = [
        {"application_id": applications[0].id, "scheduled_date": get_random_date(), "scheduled_time": get_random_time(), "duration_minutes": 60, "interviewer": "Sarah Lead", "interview_type": "video", "location": "https://meet.google.com/abc-defg-hij", "status": "scheduled"},
        {"application_id": applications[1].id, "scheduled_date": get_random_date(), "scheduled_time": get_random_time(), "duration_minutes": 45, "interviewer": "David Tech", "interview_type": "phone", "location": "555-0987", "status": "completed"},
        {"application_id": applications[4].id, "scheduled_date": get_random_date(), "scheduled_time": get_random_time(), "duration_minutes": 90, "interviewer": "John Backend", "interview_type": "onsite", "location": "Room 4B, HQ", "status": "scheduled"},
        {"application_id": applications[7].id, "scheduled_date": get_random_date(), "scheduled_time": get_random_time(), "duration_minutes": 45, "interviewer": "Alex DevOps", "interview_type": "video", "location": "https://zoom.us/j/123456789", "status": "scheduled"},
    ]

    for ivd in interviews_data:
        iv = models.Interview(**ivd)
        db.add(iv)
    
    db.commit()
    print("Database seeded with mock data successfully!")

if __name__ == "__main__":
    seed()
