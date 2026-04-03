from datetime import datetime, timedelta, timezone
from jose import jwt
from config import JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE, JWT_EXPIRE_MINUTES


def create_access_token(username: str, customer: str, allowed_tasks: list) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "customer": customer,
        "allowed_tasks": allowed_tasks,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience=JWT_AUDIENCE, issuer=JWT_ISSUER)