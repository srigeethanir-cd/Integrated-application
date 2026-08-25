from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from jose import JWTError, jwt

SECRET_KEY = "validation-only-secret-change-in-production"
ALGORITHM = "HS256"
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed_password)


def create_access_token(subject: str, expires_minutes: int = 30) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode({"sub": subject, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")
