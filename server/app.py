import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import JOBS_DIR, MAX_FILES_PER_JOB, MAX_TOTAL_UPLOAD_MB, MAX_SINGLE_FILE_MB
from jobs_db import JobDB
from worker import JobWorker
from auth import verify_user, create_access_token, require_user

app = FastAPI(title="Photo8 Secure PDF Pipeline API", version="1.0")

# ✅ CORS: production nên set IP cụ thể, tạm thời để LAN client dùng
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # production: đổi thành ["http://client-ip"] hoặc bỏ hẳn nếu WinForms không cần CORS
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = JobDB(JOBS_DIR / "jobs.sqlite")
worker = JobWorker(db)

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class JobCreateResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    created_at: str
    updated_at: str
    result: Optional[dict] = None
    error: Optional[str] = None

class LogsResponse(BaseModel):
    next_after_line: int
    lines: List[str]

@app.get("/api/v1/health")
def health():
    return {"ok": True}

@app.post("/api/v1/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    # DEBUG (remove later)
    pw = req.password if req.password is not None else ""
    print("DEBUG login username=", req.username)
    print("DEBUG password chars=", len(pw), "bytes=", len(pw.encode("utf-8")))

    if not verify_user(req.username, req.password):
        raise HTTPException(status_code=401, detail="Invalid username/password")
    token = create_access_token(req.username)
    return LoginResponse(access_token=token)

def _is_pdf_bytes(head: bytes) -> bool:
    return head.startswith(b"%PDF")

@app.post("/api/v1/jobs", response_model=JobCreateResponse)
async def create_job(
    files: List[UploadFile] = File(...),
    username: str = Depends(require_user)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if len(files) > MAX_FILES_PER_JOB:
        raise HTTPException(status_code=400, detail=f"Too many files (max {MAX_FILES_PER_JOB})")

    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    input_dir = job_dir / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    saved_count = 0

    for uf in files:
        name = (uf.filename or "").strip()
        if not name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {name}")

        # đọc file theo chunk để giới hạn size
        out_path = input_dir / Path(name).name
        written = 0
        first_chunk = b""

        with out_path.open("wb") as f:
            while True:
                chunk = await uf.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                if written == 0:
                    first_chunk = chunk[:8]
                f.write(chunk)
                written += len(chunk)
                total_bytes += len(chunk)

                if written > MAX_SINGLE_FILE_MB * 1024 * 1024:
                    raise HTTPException(status_code=400, detail=f"File too large: {name} (max {MAX_SINGLE_FILE_MB}MB)")
                if total_bytes > MAX_TOTAL_UPLOAD_MB * 1024 * 1024:
                    raise HTTPException(status_code=400, detail=f"Total upload too large (max {MAX_TOTAL_UPLOAD_MB}MB)")

        if not _is_pdf_bytes(first_chunk):
            raise HTTPException(status_code=400, detail=f"Not a valid PDF: {name}")

        saved_count += 1

    if saved_count == 0:
        raise HTTPException(status_code=400, detail="No valid PDFs found")

    log_path = str(job_dir / "job.log")
    db.create(job_id=job_id, owner=username, input_dir=str(input_dir), log_path=log_path)

    # enqueue job
    worker.enqueue(job_id)

    return JobCreateResponse(job_id=job_id, status="queued")

@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, username: str = Depends(require_user)):
    try:
        job = db.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    # ✅ owner check
    if job["owner"] != username:
        raise HTTPException(status_code=403, detail="Forbidden")

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        result=job["result"],
        error=job["error"],
    )

@app.get("/api/v1/jobs/{job_id}/logs", response_model=LogsResponse)
def get_logs(job_id: str, after_line: int = Query(default=0, ge=0), username: str = Depends(require_user)):
    try:
        job = db.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["owner"] != username:
        raise HTTPException(status_code=403, detail="Forbidden")

    log_file = Path(job["log_path"])
    if not log_file.exists():
        return LogsResponse(next_after_line=after_line, lines=[])

    lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    chunk = lines[after_line:]
    return LogsResponse(next_after_line=len(lines), lines=chunk)