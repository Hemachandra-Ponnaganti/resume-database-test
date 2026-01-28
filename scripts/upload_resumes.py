import os
import re
import json
import shutil
from datetime import datetime
from pdfminer.high_level import extract_text
from docx import Document
import subprocess

INCOMING = r"C:\Resumes\Incoming"
PROCESSED = r"C:\Resumes\Processed"

REPO_ROOT = r"C:\resume-database-test"
RESUME_DIR = os.path.join(REPO_ROOT, "resumes")
DATA_FILE = os.path.join(REPO_ROOT, "data", "resumes.json")

email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

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
    match = re.search(email_pattern, text)
    return match.group(0) if match else "Not Found"

# Load existing DB
with open(DATA_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

uploaded = 0

for file in os.listdir(INCOMING):
    if not file.lower().endswith((".pdf", ".docx")):
        continue

    src = os.path.join(INCOMING, file)
    print("Processing:", file)

    text = extract_text_from_file(src)
    name = extract_name(text)
    email = extract_email(text)

    new_name = f"{int(datetime.now().timestamp())}_{file}"
    dst = os.path.join(RESUME_DIR, new_name)

    shutil.copy(src, dst)

    db.append({
        "name": name,
        "email": email,
        "file": f"resumes/{new_name}",
        "uploaded_at": datetime.now().isoformat()
    })

    # Move file after success
    shutil.move(src, os.path.join(PROCESSED, file))
    uploaded += 1

if uploaded > 0:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

    subprocess.run(["git", "pull"], cwd=REPO_ROOT)
    subprocess.run(["git", "add", "."], cwd=REPO_ROOT)
    subprocess.run(["git", "commit", "-m", f"Added {uploaded} new resumes"], cwd=REPO_ROOT)
    subprocess.run(["git", "push"], cwd=REPO_ROOT)

print(f"✔ {uploaded} resume(s) uploaded")
