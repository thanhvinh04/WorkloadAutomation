import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from jose import jwt
from passlib.hash import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from config import JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE, JWT_EXPIRE_MINUTES, BASE_DIR

USERS_FILE = BASE_DIR / "users.json"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def _load_users():
    if not USERS_FILE.exists():
        return {}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))

def verify_user(username: str, password: str) -> bool:
    users = _load_users()
    hashed = users.get(username)
    if not hashed:
        return False
    try:
        return bcrypt.verify(password, hashed)
    except (ValueError, TypeError):
        return False

def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def require_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid/expired token")