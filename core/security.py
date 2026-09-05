from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, Request, status
from jose import jwt
from jose.exceptions import JWTError

from config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (48-char $2b$ hash)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode/validate a JWT. Raises JWTError on invalid or expired tokens."""
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


def get_current_user(request: Request) -> dict:
    """FastAPI dependency: the authenticated user's claims (id, email, role).

    Populated by ``JWTAuthMiddleware`` into ``request.scope["user"]``.
    """
    user = request.scope.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def require_roles(*roles: str):
    """FastAPI dependency factory: require the authenticated user to have one of
    the given roles (e.g. ``Depends(require_roles("admin"))``)."""

    async def _role_checker(request: Request) -> dict:
        user = get_current_user(request)
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _role_checker

