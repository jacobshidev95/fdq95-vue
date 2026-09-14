"""Application submission — accepts an uploaded resume / cover letter."""

import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter()

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("")
async def submit_application(
    job_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOC, or DOCX files are accepted.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File too large (max 10 MB)."
        )

    ext = Path(file.filename).suffix.lower() or ".pdf"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    dest = job_dir / safe_name
    dest.write_bytes(contents)

    print(
        f"[APPLICATION] job={job_id} name={name} email={email} file={safe_name}"
    )
    return {
        "ok": True,
        "job_id": job_id,
        "applicant": name,
        "email": email,
        "file": safe_name,
    }