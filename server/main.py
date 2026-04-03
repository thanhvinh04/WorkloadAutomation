import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Configure logging
log_level = logging.DEBUG
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from config import JOBS_DIR, DB_TYPE
from repositories.job_repository import JobRepository
from repositories.user_repository import UserRepository
from services.job_service import JobService
from workers.job_worker import JobWorker
from api.v1.routes.health import router as health_router
from api.v1.routes.auth import router as auth_router, set_user_repository
from api.v1.routes.jobs import router as jobs_router, set_services


def create_app() -> FastAPI:
    logger.info("Starting Photo8 API...")
    
    app = FastAPI(title="Photo8 Secure PDF Pipeline API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Database
    logger.info(f"Database type: {DB_TYPE}")
    db_path = JOBS_DIR / "jobs.sqlite"
    logger.info(f"Database path: {db_path}")
    job_repository = JobRepository(db_path)
    user_repository = UserRepository(db_path)
    logger.info("Database initialized")

    # Services
    job_service = JobService(job_repository)
    job_worker = JobWorker(job_repository)
    logger.info("Services initialized")

    # Set service containers
    set_user_repository(user_repository)
    set_services(job_service, job_worker)

    # Routes
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["jobs"])
    logger.info("Routes registered")

    logger.info("Application started successfully")
    return app


app = create_app()