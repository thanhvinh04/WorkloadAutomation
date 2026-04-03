import logging
from datetime import datetime, timedelta, timezone
from jose import jwt, ExpiredSignatureError, JWTError
from config import JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE, JWT_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


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
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    logger.debug(f"Created token for {username}")
    return token


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience=JWT_AUDIENCE, issuer=JWT_ISSUER)
        logger.debug(f"Token decoded successfully for {payload.get('sub')}")
        return payload
    except ExpiredSignatureError:
        logger.warning("Token expired")
        raise Exception("Token expired")
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        raise Exception(f"Invalid token: {e}")
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise Exception(f"Token decode error: {e}")