"""End-to-end test of all 4 features. Run against a live server.

Run with:  source venv/bin/activate && python test_api.py
"""
import io
import json
import sys
import time

import requests

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0


def check(label, ok, detail=""):
    global PASS, FAIL
    icon = "OK " if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{icon}] {label}{('  -- ' + detail) if detail else ''}")


def section(title):
    print(f"\n=== {title} ===")


# Sample resumes
RESUME_SR = """
Jane Smith
Senior Software Engineer
jane.smith@example.com  |  +1-555-0102  |  San Francisco, CA

EXPERIENCE
Senior Software Engineer, Acme Corp                       2020 - Present  (5 years)
- Built microservices with Python, FastAPI, and PostgreSQL.
- Deployed services to AWS using Docker and Kubernetes.
- Mentored 4 junior engineers; ran weekly code reviews.

Software Engineer, Initech                                2017 - 2020  (3 years)
- Developed REST APIs using Django and Node.js.
- Wrote React front-ends with Redux and TypeScript.

EDUCATION
B.S. Computer Science, MIT                                2013 - 2017

SKILLS
Python, JavaScript, TypeScript, React, Redux, FastAPI, Django,
PostgreSQL, MongoDB, Docker, Kubernetes, AWS, Git, REST API,
GraphQL, CI/CD, Machine Learning, TensorFlow, Pandas, NumPy.
"""

RESUME_MID = """
Carlos Ruiz
Mid-level Developer
carlos.ruiz@example.com  |  Madrid, Spain

EXPERIENCE
Software Developer, BetaSoft                              2021 - Present  (3 years)
- Built internal tools with Python and Flask.
- Worked with MySQL and Redis.

Junior Developer, StartupX                                2019 - 2021  (2 years)
- Front-end work in Vue.js and HTML/CSS.

SKILLS
Python, Flask, MySQL, Redis, Vue.js, HTML, CSS, Git, Linux.
"""

RESUME_JR = """
Alex Park
Junior Developer
alex.park@example.com  |  Seoul, Korea

EDUCATION
B.S. Information Systems, Korea University                 2020 - 2024

SKILLS
Python, HTML, CSS, Git, React (academic projects).
"""


def upload_resume(name, email, phone, body):
    files = {"file": ("resume.txt", body.encode("utf-8"), "text/plain")}
    data = {"full_name": name, "email": email, "phone": phone}
    r = requests.post(f"{BASE}/api/candidates/upload", data=data, files=files, timeout=15)
    return r


def main():
    # -------------------------------------------------------------- jobs
    section("Setup: jobs")
    r = requests.post(f"{BASE}/api/jobs", json={
        "title": "Senior Backend Engineer",
        "department": "Engineering",
        "location": "Remote",
        "description": (
            "We are hiring a Senior Backend Engineer to build scalable APIs "
            "using Python, FastAPI and PostgreSQL. You will deploy to AWS with "
            "Docker and Kubernetes, mentor juniors, and own services end to end."
        ),
        "required_skills": "python, fastapi, postgresql, docker, kubernetes, aws, rest api, git",
    })
    check("create job", r.status_code == 200, str(r.status_code))
    job = r.json()
    job_id = job["id"]

    # -------------------------------------------------------------- resume parsing
    section("Feature 1: Resume parsing & ranking")
    r1 = upload_resume("Jane Smith", "jane.smith@example.com", "+1-555-0102", RESUME_SR)
    check("upload senior resume", r1.status_code == 200, str(r1.status_code))
    jane = r1.json()
    check("senior: skills extracted", len(jane["skills"].split(", ")) >= 5,
          f"{len(jane['skills'].split(', '))} skills: {jane['skills'][:80]}")
    check("senior: experience > 0", jane["experience_years"] > 0,
          f"{jane['experience_years']} years")

    r2 = upload_resume("Carlos Ruiz", "carlos.ruiz@example.com", "+34-555", RESUME_MID)
    check("upload mid resume", r2.status_code == 200, str(r2.status_code))
    carlos = r2.json()
    check("mid: skills extracted", len(carlos["skills"].split(", ")) >= 3)

    r3 = upload_resume("Alex Park", "alex.park@example.com", "+82-555", RESUME_JR)
    check("upload junior resume", r3.status_code == 200, str(r3.status_code))
    alex = r3.json()

    # Idempotency: re-uploading with same email updates, not duplicates
    r1b = upload_resume("Jane Smith", "jane.smith@example.com", "+1-555-0102", RESUME_SR)
    check("re-upload same email is idempotent", r1b.json()["id"] == jane["id"])

    # Re-run upload 3 times to test stability
    for i in range(3):
        r = upload_resume("Jane Smith", "jane.smith@example.com", "+1-555-0102", RESUME_SR)
        check(f"parse stability iter {i+1}", r.status_code == 200 and r.json()["id"] == jane["id"])

    # -------------------------------------------------------------- skill matching
    section("Feature 2: Skill matching")
    apps = []
    for cand in (jane, carlos, alex):
        r = requests.post(f"{BASE}/api/applications", json={
            "job_id": job_id, "candidate_id": cand["id"]
        })
        check(f"apply {cand['full_name']}", r.status_code == 200, str(r.status_code))
        apps.append(r.json())

    # senior should rank highest
    ranked = sorted(apps, key=lambda a: a["match_score"], reverse=True)
    check("senior ranks above mid",
          ranked[0]["candidate_id"] == jane["id"],
          f"top={ranked[0]['candidate']['full_name']} score={ranked[0]['match_score']}")
    check("mid ranks above junior",
          ranked[1]["candidate_id"] == carlos["id"])
    check("match_score in 0..100",
          all(0 <= a["match_score"] <= 100 for a in apps))
    check("matched_skills populated",
          all(len(a["matched_skills"]) > 0 for a in apps))
    check("missing_skills populated for partial matches",
          any(len(a["missing_skills"]) > 0 for a in apps))

    # Per-app match detail
    r = requests.get(f"{BASE}/api/applications/{apps[0]['id']}/match")
    check("match detail endpoint", r.status_code == 200 and "score" in r.json())
    detail = r.json()
    check("match detail has matched_skills list",
          isinstance(detail["matched_skills"], list))

    # -------------------------------------------------------------- ranking endpoint
    r = requests.get(f"{BASE}/api/jobs/{job_id}/ranked-candidates")
    check("ranked-candidates endpoint", r.status_code == 200)
    data = r.json()
    check("ranked: 3 results", len(data["results"]) == 3)
    scores = [x["match_score"] for x in data["results"]]
    check("ranked: descending order", scores == sorted(scores, reverse=True),
          f"scores={scores}")
    check("ranked: top result is Jane",
          data["results"][0]["candidate_name"] == "Jane Smith")

    # -------------------------------------------------------------- pipeline
    section("Feature 3: Hiring pipeline visualization")
    # Move candidates through stages
    stages_for = {jane["id"]: "interview", carlos["id"]: "screening", alex["id"]: "rejected"}
    for app_row in apps:
        new_stage = stages_for[app_row["candidate_id"]]
        r = requests.patch(f"{BASE}/api/applications/{app_row['id']}/stage",
                           params={"stage": new_stage})
        check(f"move {app_row['candidate']['full_name']} -> {new_stage}",
              r.status_code == 200 and r.json()["stage"] == new_stage)

    # Invalid stage
    r = requests.patch(f"{BASE}/api/applications/{apps[0]['id']}/stage",
                       params={"stage": "nope"})
    check("reject invalid stage", r.status_code == 400)

    # Pipeline view
    r = requests.get(f"{BASE}/api/pipeline")
    check("pipeline view all jobs", r.status_code == 200)
    p = r.json()
    cols = {c["stage"]: len(c["applications"]) for c in p["columns"]}
    check("pipeline: columns present",
          set(cols.keys()) == {"applied", "screening", "interview", "offer", "hired", "rejected"},
          f"got {cols}")
    check("pipeline: 1 interview", cols["interview"] == 1)
    check("pipeline: 1 screening", cols["screening"] == 1)
    check("pipeline: 1 rejected", cols["rejected"] == 1)

    # Pipeline scoped to job
    r = requests.get(f"{BASE}/api/pipeline", params={"job_id": job_id})
    check("pipeline scoped to job", r.status_code == 200)
    total = sum(len(c["applications"]) for c in r.json()["columns"])
    check("scoped pipeline has 3 apps", total == 3, f"total={total}")

    # Move again - hired
    r = requests.patch(f"{BASE}/api/applications/{apps[0]['id']}/stage",
                       params={"stage": "hired"})
    check("move Jane -> hired", r.status_code == 200 and r.json()["stage"] == "hired")
    r = requests.get(f"{BASE}/api/pipeline", params={"job_id": job_id})
    cols = {c["stage"]: len(c["applications"]) for c in r.json()["columns"]}
    check("pipeline: hired column has 1", cols["hired"] == 1)

    # -------------------------------------------------------------- interviews
    section("Feature 4: Interview scheduling")
    jane_app_id = apps[0]["id"]
    interviews = []
    # Create 3 interviews at different times
    for i, (d, t) in enumerate([
        ("2026-08-01", "10:00:00"),
        ("2026-08-03", "14:30:00"),
        ("2026-08-05", "09:15:00"),
    ]):
        r = requests.post(f"{BASE}/api/interviews", json={
            "application_id": jane_app_id,
            "scheduled_date": d,
            "scheduled_time": t,
            "duration_minutes": 45,
            "interviewer": f"Tech Lead {i+1}",
            "interview_type": "video",
            "location": f"https://meet.example.com/abc-{i}",
            "notes": f"Round {i+1}",
        })
        check(f"schedule interview {i+1}", r.status_code == 200, str(r.status_code))
        interviews.append(r.json())

    # Interview should advance stage to interview
    r = requests.get(f"{BASE}/api/applications/{jane_app_id}")
    # Jane was moved to 'hired' above; scheduling more interviews is allowed
    check("app still exists", r.status_code == 200)

    # Stage auto-advances from screening -> interview for carlos
    carlos_app_id = next(a["id"] for a in apps if a["candidate_id"] == carlos["id"])
    r = requests.post(f"{BASE}/api/interviews", json={
        "application_id": carlos_app_id,
        "scheduled_date": "2026-08-10",
        "scheduled_time": "11:00:00",
        "duration_minutes": 60,
        "interviewer": "Eng Manager",
        "interview_type": "phone",
        "location": "+1-555-9999",
    })
    check("schedule carlos interview", r.status_code == 200)
    r = requests.get(f"{BASE}/api/applications/{carlos_app_id}")
    check("carlos auto-advanced to interview",
          r.json()["stage"] == "interview",
          f"stage={r.json()['stage']}")

    # List interviews
    r = requests.get(f"{BASE}/api/interviews")
    check("list interviews", r.status_code == 200 and len(r.json()) == 4)

    # Filter by application
    r = requests.get(f"{BASE}/api/interviews", params={"application_id": jane_app_id})
    check("filter by app", r.status_code == 200 and len(r.json()) == 3)

    # Update interview
    iid = interviews[0]["id"]
    r = requests.patch(f"{BASE}/api/interviews/{iid}", json={
        "interviewer": "Senior Eng Lead",
        "location": "https://meet.example.com/new-room",
        "notes": "Updated agenda",
    })
    check("update interview", r.status_code == 200)
    check("update applied", r.json()["interviewer"] == "Senior Eng Lead")

    # Cancel
    r = requests.delete(f"{BASE}/api/interviews/{iid}")
    check("cancel interview", r.status_code == 200 and r.json()["cancelled"])
    r = requests.get(f"{BASE}/api/interviews/{iid}")
    check("status = cancelled", r.json()["status"] == "cancelled")

    # Invalid application id
    r = requests.post(f"{BASE}/api/interviews", json={
        "application_id": 9999,
        "scheduled_date": "2026-08-01",
        "scheduled_time": "10:00:00",
    })
    check("reject interview for missing app", r.status_code == 404)

    # -------------------------------------------------------------- bad input
    section("Robustness")
    r = requests.get(f"{BASE}/api/jobs/9999")
    check("404 on missing job", r.status_code == 404)
    r = requests.get(f"{BASE}/api/candidates/9999")
    check("404 on missing candidate", r.status_code == 404)
    r = requests.post(f"{BASE}/api/candidates", json={
        "full_name": "Dup", "email": "jane.smith@example.com"
    })
    check("reject duplicate email", r.status_code == 400)

    print(f"\n--- TOTALS: {PASS} pass, {FAIL} fail ---")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
