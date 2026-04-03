import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING
from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from config import JOBS_DIR
from models.schemas import JobCreateResponse, JobStatusResponse, LogsResponse
from core.security import decode_token
from core.config_loader import config_loader
from core.job_logger import job_logger

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from services.job_service import JobService
    from workers.job_worker import JobWorker

router = APIRouter()


class ServiceContainer:
    job_service: "JobService"
    job_worker: "JobWorker"


container = ServiceContainer()


def set_services(service: "JobService", worker: "JobWorker"):
    container.job_service = service
    container.job_worker = worker


def _is_pdf_bytes(head: bytes) -> bool:
    return head.startswith(b"%PDF")


@router.post("", response_model=JobCreateResponse)
async def create_job(
    files: list[UploadFile] = File(...),
    task_code: str = Query(..., description="Task code"),
    token: str = Query(None, description="JWT token"),
):
    logger.info(f"Create job request - task_code: {task_code}, token present: {bool(token)}")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if not token:
        logger.warning("Missing token in request")
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = decode_token(token)
        logger.info(f"Token decoded for user: {payload.get('sub')}")
    except Exception as e:
        logger.error(f"Token decode failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    username = payload.get("sub")
    customer = payload.get("customer", "")
    allowed_tasks = payload.get("allowed_tasks", [])

    task_config = config_loader.get_task_config(task_code)
    if not task_config:
        logger.warning(f"Task {task_code} not found")
        raise HTTPException(status_code=400, detail=f"Task {task_code} not found")

    if task_code not in allowed_tasks:
        logger.warning(f"Task {task_code} not allowed for user {username}")
        raise HTTPException(status_code=403, detail=f"Task {task_code} not allowed")

    # Clear old job logs - keep only last 5 jobs
    job_logger.clear_old_logs(JOBS_DIR, keep_last=5)

    max_files = config_loader.get("upload.max_files_per_job", 50)
    max_size = config_loader.get("upload.max_single_file_mb", 50)
    max_total = config_loader.get("upload.max_total_upload_mb", 200)

    if len(files) > max_files:
        raise HTTPException(status_code=400, detail=f"Too many files (max {max_files})")

    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    input_dir = job_dir / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)

    # Get job logger
    jlog = job_logger.get_logger(job_id, job_dir)
    jlog.info(f"Starting job {job_id} for task {task_code}")
    jlog.info(f"User: {username}, Customer: {customer}")

    total_bytes = 0
    saved_count = 0
    input_types = task_config.get("input_types", [".pdf"])

    for uf in files:
        name = (uf.filename or "").strip()
        ext = Path(name).suffix.lower()
        
        if ext not in input_types:
            jlog.error(f"Invalid file type: {name}")
            raise HTTPException(status_code=400, detail=f"Invalid file type: {name}. Allowed: {input_types}")

        out_path = input_dir / Path(name).name
        written = 0
        first_chunk = b""

        with out_path.open("wb") as f:
            while True:
                chunk = await uf.read(1024 * 1024)
                if not chunk:
                    break
                if written == 0:
                    first_chunk = chunk[:8]
                f.write(chunk)
                written += len(chunk)
                total_bytes += len(chunk)

                if written > max_size * 1024 * 1024:
                    jlog.error(f"File too large: {name}")
                    raise HTTPException(status_code=400, detail=f"File too large: {name}")
                if total_bytes > max_total * 1024 * 1024:
                    jlog.error(f"Total upload too large")
                    raise HTTPException(status_code=400, detail=f"Total upload too large")

        if ext == ".pdf" and not _is_pdf_bytes(first_chunk):
            jlog.error(f"Not a valid PDF: {name}")
            raise HTTPException(status_code=400, detail=f"Not a valid PDF: {name}")

        jlog.info(f"Saved file: {name}")
        saved_count += 1

    if saved_count == 0:
        jlog.error("No valid files found")
        raise HTTPException(status_code=400, detail="No valid files found")

    log_path = str(job_dir / "job.log")
    container.job_service.repo.create(job_id=job_id, owner=username, input_dir=str(input_dir), log_path=log_path)
    container.job_service.repo.update(job_id, task_code=task_code)

    container.job_worker.enqueue(job_id, task_code)

    jlog.info(f"Job {job_id} queued successfully")
    logger.info(f"Job created: {job_id} for task {task_code}")
    return JobCreateResponse(job_id=job_id, status="queued", task_code=task_code)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, token: str = Query(None, description="JWT token")):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    return container.job_service.get_job(job_id, username)


@router.get("/{job_id}/logs", response_model=LogsResponse)
def get_logs(job_id: str, after_line: int = Query(default=0, ge=0), token: str = Query(None, description="JWT token")):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    result = container.job_service.get_job_logs(job_id, username, after_line)
    return LogsResponse(next_after_line=result["next_after_line"], lines=result["lines"])