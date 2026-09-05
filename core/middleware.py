import logging
import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional, Set, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from jose.exceptions import JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from core.security import decode_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("request_logger")


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Paths that never require authentication (docs, health, auth, stripe webhook).
PUBLIC_PATHS: Tuple[str, ...] = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/auth/",
    "/webhooks",
)

# Rate limiting (per client IP, fixed window).
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "120"))       # general API
AUTH_RATE_LIMIT_MAX = int(os.getenv("AUTH_RATE_LIMIT_MAX", "10"))  # /auth/*

# Role-based access control policy:
#   (HTTP methods, path prefix, roles allowed)
# Requests not matching any rule are allowed for ANY authenticated user.
# Public paths bypass role checks entirely.
ROLE_POLICIES: List[Tuple[Set[str], str, Set[str]]] = [
    # Content management - instructors and admins can create/update/delete
    ({"POST", "PUT", "DELETE"}, "/courses", {"instructor", "admin"}),
    ({"POST", "PUT", "DELETE"}, "/lessons", {"instructor", "admin"}),
    ({"POST", "PUT", "DELETE"}, "/quizzes", {"instructor", "admin"}),
    ({"POST", "PUT", "DELETE"}, "/questions", {"instructor", "admin"}),
    # Moderation - only admins can delete submissions / progress
    ({"DELETE"}, "/submissions", {"admin"}),
    ({"DELETE"}, "/progress", {"admin"}),
    # Admin area
    ({"*"}, "/admin", {"admin"}),
]


def is_public_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PUBLIC_PATHS)


# --------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------

def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory fixed-window rate limiter, keyed by client IP.

    General endpoints: RATE_LIMIT_MAX requests per window.
    Auth endpoints (register/login) get a stricter limit to slow brute force.
    """

    def __init__(self, app):
        super().__init__(app)
        # Bucket keyed by (client_ip, "general" | "auth") so general traffic
        # does not consume the stricter auth budget.
        self._hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Never interrupt CORS preflight / WebSocket upgrades.
        if request.method == "OPTIONS":
            return await call_next(request)

        ip = _client_ip(request)
        bucket = "auth" if request.url.path.startswith("/auth/") else "general"
        limit = AUTH_RATE_LIMIT_MAX if bucket == "auth" else RATE_LIMIT_MAX
        key = (ip, bucket)
        window = RATE_LIMIT_SECONDS

        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > window:
            hits.popleft()

        if len(hits) >= limit:
            retry_after = int(window - (now - hits[0])) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded, slow down"},
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        response = await call_next(request)
        return response


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Validates JWT (Bearer header or ``access_token`` cookie) and attaches
    the user claims (id, email, role) to ``request.scope["user"]``.

    Public paths are skipped. Missing / invalid tokens on protected paths
    return 401.
    """

    @staticmethod
    def _extract_token(request: Request) -> Optional[str]:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip()
        return request.cookies.get("access_token")

    async def dispatch(self, request: Request, call_next):
        # Clean slate for every request
        request.scope["user"] = None

        if request.method == "OPTIONS" or is_public_path(request.url.path):
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=401, content={"detail": "Not authenticated"}
            )

        try:
            claims = decode_token(token)
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        request.scope["user"] = {
            "id": claims.get("user_id"),
            "email": claims.get("sub"),
            "role": claims.get("role", "student"),
        }
        return await call_next(request)


class RoleAccessMiddleware(BaseHTTPMiddleware):
    """Enforces role-based access based on ``ROLE_POLICIES``.

    Runs AFTER ``JWTAuthMiddleware`` so the authenticated user is available in
    ``request.scope["user"]``.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS" or is_public_path(path):
            return await call_next(request)

        user = request.scope.get("user")
        if not user:
            # Auth middleware already rejected it; keep a sensible default.
            return JSONResponse(
                status_code=401, content={"detail": "Not authenticated"}
            )

        role = (user.get("role") or "student").lower()
        method = request.method.upper()

        for methods, prefix, allowed_roles in ROLE_POLICIES:
            if path.startswith(prefix) and (
                "*" in methods or method in methods
            ):
                if role not in allowed_roles:
                    logger.info(
                        f"403 role check: {method} {path} role={role} "
                        f"requires={allowed_roles}"
                    )
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Insufficient permissions"},
                    )
                break

        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000  # in ms
        logger.info(
            f"{request.method} {request.url.path} completed_in={process_time:.2f}ms "
            f"status_code={response.status_code}"
        )

        # Add custom header with response time
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response

