from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer: str
    allowed_tasks: List[str]


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    task_code: str


class JobStatusResponse(BaseModel):
    job_id: str
    task_code: str
    status: str
    progress: float
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LogsResponse(BaseModel):
    next_after_line: int
    lines: List[str]


class HealthResponse(BaseModel):
    ok: bool
    version: str = "1.0.0"