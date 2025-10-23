from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_BCRYPT_BYTES = 72

def hash_password(password: str) -> str:
    data = password.encode("utf-8")
    if len(data) > MAX_BCRYPT_BYTES:
        # Prefer rejecting with a clear message over silent truncation
        raise ValueError("Password is too long for bcrypt (max 72 bytes when UTF-8 encoded)")
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    # For verification, bcrypt library handles the check; no need to truncate here,
    # but inputs longer than 72 bytes would never have been hashed in the first place if you enforce the limit.
    return pwd_context.verify(plain, hashed)
