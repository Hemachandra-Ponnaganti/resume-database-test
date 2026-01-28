import os
import re
import json
import shutil
import subprocess
from datetime import datetime
from pdfminer.high_level import extract_text
from docx import Document

# ---------------- PATH CONFIG ----------------
INCOMING = r"C:\Resumes\Incoming"
PROCESSED = r"C:\Resumes\Processed"

REPO_ROOT = r"C:\resume-database-test"
RESUME_DIR = os.path.join(REPO_ROOT, "resumes")
DATA_FILE = os.path.join(REPO_ROOT, "data", "resumes.json")
# --------------------------------------------

# ---------------- ROLE & SKILLS ----------------
ROLE_SKILLS = {
    "Frontend Developer": [
        "html", "css", "javascript", "react", "angular", "vue",
        "redux", "typescript", "bootstrap"
    ],
    "Backend Developer": [
        "java", "spring", "spring boot", "python", "django",
        "flask", "node", "express", "php", "laravel"
    ],
    "Full Stack Developer": [
        "javascript", "react", "node", "java",
        "spring", "mongodb", "mysql"
    ],
    "Data Analyst": [
        "sql", "excel", "power bi", "tableau",
        "python", "pandas", "numpy"
    ],
    "DevOps Engineer": [
        "docker", "kubernetes", "aws", "azure",
        "jenkins", "linux", "terraform"
    ],
    "Digital Marketing Executive": [
        "seo", "sem", "google ads", "facebook ads",
        "social media", "content marketing", "email marketing",
        "analytics", "campaign"
    ],
    "Graphic Designer": [
        "photoshop", "illustrator", "figma",
        "ui", "ux", "adobe", "coreldraw", "canva"
    ],
    "HR / Recruiter": [
        "recruitment", "talent acquisition", "hr",
        "onboarding", "payroll", "screening",
        "employee engagement"
    ],
    "Finance / Accounts": [
        "accounting", "tally", "gst", "taxation",
        "finance", "auditing", "balance sheet"
    ],
    "Operations / Admin": [
        "operations", "administration", "coordination",
        "vendor management", "office management"
    ]
}
# ------------------------------------------------

EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# ---------------- EXTRACTION FUNCTIONS ----------------
def extract_text_from_file(path):
    if path.lower().endswith(".pdf"):
        return extract_text(path)
    elif path.lower().endswith(".docx"):
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def extract_name(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:10]:
        if 1 <= len(line.split()) <= 4 and len(line) <= 40:
            return line
    return "Unknown"

def extract_email(text):
    match = re.search(EMAIL_PATTERN, text)
    return match.group(0) if match else "Not Found"

def extract_experience(text):
    patterns = [
        r"(\d+\.?\d*)\+?\s*(years|year|yrs|yr)",
        r"experience\s*[:\-]?\s*(\d+\.?\d*)"
    ]
    for p in patterns:
        match = re.search(p, text.lower())
        if match:
            return match.group(1) + " years"
    return "Not Mentioned"

def extract_qualification(text):
    qualifications = [
        "b.tech", "b.e", "m.tech", "mba", "mca",
        "b.sc", "m.sc", "b.com", "degree", "diploma"
    ]
    found = []
    t = text.lower()
    for q in qualifications:
        if q in t:
            found.append(q.upper())
    return ", ".join(set(found)) if found else "Not Mentioned"

def extract_skills(text):
    text_lower = text.lower()
    found = set()
    for skills in ROLE_SKILLS.values():
        for s in skills:
            if s in text_lower:
                found.add(s)
    return list(found)

def assign_role(skills):
    scores = {}
    for role, role_skills in ROLE_SKILLS.items():
        scores[role] = sum(1 for s in skills if s in role_skills)

    best_role = max(scores, key=scores.get)
    return best_role if scores[best_role] > 0 else "Uncategorized"
# -----------------------------------------------------

# ---------------- LOAD DATABASE ----------------
with open(DATA_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

uploaded = 0

# ---------------- PROCESS FILES ----------------
for file in os.listdir(INCOMING):
    if not file.lower().endswith((".pdf", ".docx")):
        continue

    src = os.path.join(INCOMING, file)
    print("Processing:", file)

    text = extract_text_from_file(src)

    name = extract_name(text)
    email = extract_email(text)
    experience = extract_experience(text)
    qualification = extract_qualification(text)
    skills = extract_skills(text)
    role = assign_role(skills)

    new_name = f"{int(datetime.now().timestamp())}_{file}"
    shutil.copy(src, os.path.join(RESUME_DIR, new_name))

    db.append({
        "name": name,
        "email": email,
        "role": role,
        "skills": skills,
        "experience": experience,
        "qualification": qualification,
        "file": f"resumes/{new_name}",
        "uploaded_at": datetime.now().isoformat()
    })

    shutil.move(src, os.path.join(PROCESSED, file))
    uploaded += 1

# ---------------- SAVE & PUSH ----------------
if uploaded > 0:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

    subprocess.run(["git", "pull"], cwd=REPO_ROOT)
    subprocess.run(["git", "add", "."], cwd=REPO_ROOT)
    subprocess.run(["git", "commit", "-m", f"Added {uploaded} resumes"], cwd=REPO_ROOT)
    subprocess.run(["git", "push"], cwd=REPO_ROOT)

print(f"✔ {uploaded} resume(s) uploaded successfully")
