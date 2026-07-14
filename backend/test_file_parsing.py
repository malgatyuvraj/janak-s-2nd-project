"""Test resume parsing for PDF and DOCX files."""
import io
import sys
import requests

from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE = "http://127.0.0.1:8000"

RESUME_TEXT = """
Priya Patel
Data Scientist
priya.patel@example.com  +1-555-2025

EXPERIENCE
Senior Data Scientist, FinTech Co               2021 - Present (4 years)
- Built ML pipelines in Python with TensorFlow and PyTorch.
- Deployed models to AWS using Docker.

Data Analyst, RetailCo                          2018 - 2021 (3 years)
- Wrote SQL queries against PostgreSQL.
- Pandas and NumPy analysis.

SKILLS
Python, SQL, TensorFlow, PyTorch, PostgreSQL, AWS, Docker,
Machine Learning, NLP, Pandas, NumPy.
"""


def make_docx() -> bytes:
    doc = Document()
    for line in RESUME_TEXT.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 750
    for line in RESUME_TEXT.split("\n"):
        c.drawString(50, y, line.strip())
        y -= 16
    c.save()
    return buf.getvalue()


def test_pdf():
    print("=== PDF upload ===")
    files = {"file": ("resume.pdf", make_pdf(), "application/pdf")}
    data = {"full_name": "Priya Patel", "email": "priya.pdf@example.com", "phone": ""}
    r = requests.post(f"{BASE}/api/candidates/upload", data=data, files=files, timeout=20)
    print("status:", r.status_code)
    if r.status_code != 200:
        print("body:", r.text)
        return False
    j = r.json()
    print("id:", j["id"])
    print("skills:", j["skills"])
    print("experience:", j["experience_years"])
    ok = "python" in j["skills"].lower() and "tensorflow" in j["skills"].lower()
    print("OK" if ok else "FAIL")
    return ok


def test_docx():
    print("\n=== DOCX upload ===")
    files = {"file": ("resume.docx", make_docx(),
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"full_name": "Priya Patel", "email": "priya.docx@example.com", "phone": ""}
    r = requests.post(f"{BASE}/api/candidates/upload", data=data, files=files, timeout=20)
    print("status:", r.status_code)
    if r.status_code != 200:
        print("body:", r.text)
        return False
    j = r.json()
    print("id:", j["id"])
    print("skills:", j["skills"])
    print("experience:", j["experience_years"])
    ok = "python" in j["skills"].lower() and "tensorflow" in j["skills"].lower()
    print("OK" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    ok_pdf = test_pdf()
    ok_docx = test_docx()
    sys.exit(0 if (ok_pdf and ok_docx) else 1)
