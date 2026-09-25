import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import bcrypt

from app.core.config import settings

# Initialize Argon2 hasher with secure parameters
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against an Argon2 or Bcrypt hash.
    Safely handles both Argon2 and Bcrypt legacy hashes.
    """
    if not hashed_password or not plain_password:
        return False
    
    # Try Argon2 verification first
    if hashed_password.startswith("$argon2"):
        try:
            return ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False
            
    # Try Bcrypt verification
    if hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$"):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2id.
    """
    return ph.hash(password)


def create_access_token(
    subject: Union[str, Any],
    tenant_id: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token containing subject (user_id), tenant_id, role, and expiry.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: Union[str, Any],
    tenant_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT refresh token for session renewal.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises jwt.PyJWTError on invalid/expired tokens.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
