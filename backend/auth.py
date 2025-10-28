# backend/auth.py  (versión final con Argon2)
import os
import jwt
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher

ph = PasswordHasher()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change")
JWT_ALG = "HS256"
ACCESS_TTL_MIN = int(os.getenv("ACCESS_TTL_MIN", "60"))

def hash_password(plain: str) -> str:
    print("[AUTH] hashing with ARGON2, len:", len(plain))
    return ph.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, plain)
        return True
    except Exception:
        return False

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": int(now.timestamp()),
               "exp": int((now + timedelta(minutes=ACCESS_TTL_MIN)).timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
