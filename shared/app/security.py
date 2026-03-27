from datetime import datetime, timedelta, timezone
import hashlib

from jose import jwt

from .config import settings


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def create_access_token(subject: str, claims: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_exp_minutes)
    payload = {
        'sub': subject,
        'iss': settings.jwt_issuer,
        'aud': settings.jwt_audience,
        'exp': expire,
        **claims,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm='HS256')


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=['HS256'],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
