from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List

import sqlite3
import os
from datetime import datetime
from fastapi.security import HTTPBasic, HTTPBasicCredentials


app = FastAPI(title="Lead Management APIs")
security = HTTPBasic()

# Database
DB_NAME = "leads.db"
UPLOAD_DIR = "resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def init_db():
    """Initialize the SQLite database with the leads table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  first_name TEXT NOT NULL,
                  last_name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  resume_path TEXT NOT NULL,
                  state TEXT DEFAULT 'PENDING',
                  created_at TEXT NOT NULL)"""
    )
    conn.commit()
    conn.close()


init_db()


class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: str


class LeadResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    resume_path: str
    state: str
    created_at: datetime


def save_file(file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    return file_path


def send_email(to: str, subject: str, body: str):
    ## I DID NOT IMPLEMENT THE EMAIL FUNCTIONALITY
    ## AS IT REQUIRES SMTP SERVER CONFIGURATION
    ## JUST ADDING A PLACEHOLDER FUNCTION FOR EMAIL SENDING
    print(f"[EMAIL] To: {to}, Subject: {subject}, Body: {body}")


def get_db_connection():

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):

    if credentials.username != "attorney" or credentials.password != "devpass":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username


@app.post("/leads/", response_model=LeadResponse)
async def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
):
    resume_path = save_file(resume)
    created_at = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leads (first_name, last_name, email, resume_path, created_at) VALUES (?, ?, ?, ?, ?)",
        (first_name, last_name, email, resume_path, created_at.isoformat()),
    )
    lead_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()
    conn.close()

    # email notification
    send_email(
        email, "Lead Submitted", f"Hello {first_name}, your lead has been received!"
    )
    send_email(
        "attorney@company.com", "New Lead", f"New lead from {first_name} {last_name}"
    )

    return {
        "id": lead["id"],
        "first_name": lead["first_name"],
        "last_name": lead["last_name"],
        "email": lead["email"],
        "resume_path": lead["resume_path"],
        "state": lead["state"],
        "created_at": datetime.fromisoformat(lead["created_at"]),
    }


@app.get("/leads/", response_model=List[LeadResponse])
async def get_all_leads(username: str = Depends(check_credentials)):

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads")
    leads = cursor.fetchall()
    conn.close()
    return [
        {
            "id": lead["id"],
            "first_name": lead["first_name"],
            "last_name": lead["last_name"],
            "email": lead["email"],
            "resume_path": lead["resume_path"],
            "state": lead["state"],
            "created_at": datetime.fromisoformat(lead["created_at"]),
        }
        for lead in leads
    ]


@app.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead_state(lead_id: int, username: str = Depends(check_credentials)):
    ## THIS WILL UPDATE THE LEAD STATE TO "REACHED_OUT"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()

    if not lead:
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead["state"] != "PENDING":
        conn.close()
        raise HTTPException(status_code=400, detail="Can only update PENDING leads")

    cursor.execute("UPDATE leads SET state = 'REACHED_OUT' WHERE id = ?", (lead_id,))
    conn.commit()

    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    updated_lead = cursor.fetchone()
    conn.close()

    return {
        "id": updated_lead["id"],
        "first_name": updated_lead["first_name"],
        "last_name": updated_lead["last_name"],
        "email": updated_lead["email"],
        "resume_path": updated_lead["resume_path"],
        "state": updated_lead["state"],
        "created_at": datetime.fromisoformat(
            updated_lead["created_at"]
        ),  # Convert to datetime
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting Lead Management API...")
    print("Test credentials: attorney/devpass")
    print("Try POST /leads/ with form data: first_name, last_name, email, resume")
    print("Try GET /leads/ and PATCH /leads/{id} with Basic Auth")
    uvicorn.run(app, host="0.0.0.0", port=8000)
