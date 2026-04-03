import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env that sits next to config.py (portable)
load_dotenv(dotenv_path=BASE_DIR / ".env")

STORAGE_DIR = BASE_DIR / "storage"
JOBS_DIR = STORAGE_DIR / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# ==== Secrets / Security ====
JWT_SECRET = os.environ.get("PHOTO8_JWT_SECRET", "")
if not JWT_SECRET:
    raise RuntimeError(
        "Missing PHOTO8_JWT_SECRET. Put it in server/.env or set Windows environment variable."
    )

JWT_ISSUER = os.environ.get("PHOTO8_JWT_ISSUER", "photo8-api")
JWT_AUDIENCE = os.environ.get("PHOTO8_JWT_AUDIENCE", "photo8-client")
JWT_EXPIRE_MINUTES = int(os.environ.get("PHOTO8_JWT_EXPIRE_MINUTES", "120"))

# ==== Upload limits ====
MAX_FILES_PER_JOB = int(os.environ.get("PHOTO8_MAX_FILES_PER_JOB", "50"))
MAX_TOTAL_UPLOAD_MB = int(os.environ.get("PHOTO8_MAX_TOTAL_UPLOAD_MB", "200"))
MAX_SINGLE_FILE_MB = int(os.environ.get("PHOTO8_MAX_SINGLE_FILE_MB", "50"))

# ==== Python pipeline on server ====
PYTHON_EXE = os.environ.get(
    "PHOTO8_PYTHON_EXE",
    str((BASE_DIR / ".venv" / "Scripts" / "python.exe").resolve()),
)
PDF_TO_SQL_SCRIPT = os.environ.get("PHOTO8_PDF_TO_SQL_SCRIPT", str(BASE_DIR / "BU1_HADDAD_PDFToSQL.py"))
SQL_TO_SHEET_SCRIPT = os.environ.get("PHOTO8_SQL_TO_SHEET_SCRIPT", str(BASE_DIR / "BU1_HADDAD_SQLToGoogleSheet.py"))
DESIGNCHART_SCRIPT = os.environ.get(
    "PHOTO8_DESIGNCHART_SCRIPT",
    str(BASE_DIR.parent / "designchart_parser" / "main.py")
)

WORKER_CONCURRENCY = 1