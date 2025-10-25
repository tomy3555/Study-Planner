# backend/auth.py
import os
import jwt
from datetime import datetime, timedelta, timezone
from passlib.hash import bcrypt_sha256  # 👈 en lugar de bcrypt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change")
JWT_ALG = "HS256"
ACCESS_TTL_MIN = int(os.getenv("ACCESS_TTL_MIN", "60"))

def hash_password(plain: str) -> str:
    # bcrypt_sha256: primero SHA-256, luego bcrypt (evita límite 72B)
    return bcrypt_sha256.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt_sha256.verify(plain, hashed)
    except Exception:
        return False

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TTL_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
