import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import RefreshToken, User
from schemas import RegisterRequest

SECRET = b"stage3-validation-signing-key"

class InvalidCredentialsError(Exception):
    pass
class InvalidTokenError(Exception):
    pass

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}:{digest.hex()}"
def verify_password(password: str, encoded: str) -> bool:
    salt_hex, expected = encoded.split(":", 1)
    actual = hash_password(password, bytes.fromhex(salt_hex)).split(":", 1)[1]
    return hmac.compare_digest(actual, expected)
def encode_token(subject: str, kind: str, token_id: str, lifetime: int) -> str:
    payload = {"sub": subject, "kind": kind, "jti": token_id, "exp": int(time.time()) + lifetime}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
    signature = base64.urlsafe_b64encode(hmac.new(SECRET, body, hashlib.sha256).digest()).rstrip(b"=")
    return f"{body.decode()}.{signature.decode()}"
def decode_token(token: str, expected_kind: str) -> dict:
    try:
        body_text, signature_text = token.split(".", 1)
        body = body_text.encode()
        expected = base64.urlsafe_b64encode(hmac.new(SECRET, body, hashlib.sha256).digest()).rstrip(b"=").decode()
        if not hmac.compare_digest(signature_text, expected):
            raise InvalidTokenError("invalid signature")
        payload = json.loads(base64.urlsafe_b64decode(body + b"=" * (-len(body) % 4)))
        if payload["kind"] != expected_kind or payload["exp"] < time.time():
            raise InvalidTokenError("expired or incorrect token")
        return payload
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        raise InvalidTokenError("malformed token") from error
def register(db: Session, payload: RegisterRequest) -> User:
    if db.scalar(select(User).where(User.username == payload.username)):
        raise ValueError("username already registered")
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user); db.commit(); db.refresh(user); return user
def authenticate(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("invalid username or password")
    return user
def issue_pair(db: Session, user: User) -> tuple[str, str]:
    access_id, refresh_id = str(uuid.uuid4()), str(uuid.uuid4())
    db.add(RefreshToken(token_id=refresh_id, user=user)); db.commit()
    return encode_token(str(user.id), "access", access_id, 900), encode_token(str(user.id), "refresh", refresh_id, 86_400)
def rotate_refresh(db: Session, token: str) -> tuple[str, str]:
    payload = decode_token(token, "refresh")
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_id == payload["jti"]))
    if stored is None or stored.revoked:
        raise InvalidTokenError("refresh token revoked")
    stored.revoked = True; db.commit()
    return issue_pair(db, stored.user)
