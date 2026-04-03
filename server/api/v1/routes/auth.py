import logging
from typing import Optional
from fastapi import APIRouter, HTTPException

from core.security import create_access_token
from repositories.user_repository import UserRepository
from models.schemas import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)

router = APIRouter()

user_repository: Optional[UserRepository] = None


def set_user_repository(repo: UserRepository):
    global user_repository
    user_repository = repo


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    logger.info(f"Login attempt: username={req.username}")
    
    if not user_repository:
        logger.error("User repository not initialized")
        raise HTTPException(status_code=500, detail="User repository not initialized")

    user = user_repository.get_user(req.username)
    if not user:
        logger.warning(f"User not found: {req.username}")
        raise HTTPException(status_code=401, detail="Invalid username/password")

    if not user_repository.verify_password(req.username, req.password):
        logger.warning(f"Invalid password for user: {req.username}")
        raise HTTPException(status_code=401, detail="Invalid username/password")

    token = create_access_token(req.username, user["customer"], user["allowed_tasks"])
    logger.info(f"Login success: username={req.username}, customer={user['customer']}")

    return LoginResponse(access_token=token, customer=user["customer"], allowed_tasks=user["allowed_tasks"])