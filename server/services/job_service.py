import uuid
from pathlib import Path
from typing import Dict, Any

from repositories.job_repository import JobRepository
from core.exceptions import NotFoundException, ForbiddenException
from models.schemas import JobStatusResponse


class JobService:
    def __init__(self, repository: JobRepository):
        self.repository = repository

    @property
    def repo(self) -> JobRepository:
        return self.repository

    def create_job(self, owner: str, task_code: str, input_dir: Path) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        self.repository.create(job_id=job_id, owner=owner, input_dir=str(input_dir), log_path=str(input_dir / "job.log"))
        self.repository.update(job_id, task_code=task_code)
        return {"job_id": job_id, "status": "queued", "task_code": task_code}

    def get_job(self, job_id: str, username: str) -> JobStatusResponse:
        try:
            job = self.repository.get(job_id)
        except KeyError:
            raise NotFoundException(f"Job {job_id} not found")
        if job["owner"] != username:
            raise ForbiddenException()
        return JobStatusResponse(
            job_id=job["job_id"],
            task_code=job.get("task_code", ""),
            status=job["status"],
            progress=job["progress"],
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            result=job["result"],
            error=job["error"],
        )

    def get_job_logs(self, job_id: str, username: str, after_line: int = 0) -> Dict[str, Any]:
        try:
            job = self.repository.get(job_id)
        except KeyError:
            raise NotFoundException(f"Job {job_id} not found")
        if job["owner"] != username:
            raise ForbiddenException()
        log_file = Path(job["log_path"])
        if not log_file.exists():
            return {"next_after_line": after_line, "lines": []}
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return {"next_after_line": len(lines), "lines": lines[after_line:]}