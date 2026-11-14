"""
auth_routes.py -- FastAPI authentication & entitlement routes for Plenary Suite.

Endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
  GET  /api/auth/entitlements

Uses PyJWT if installed, otherwise falls back to stdlib HMAC-SHA256 JWT tokens.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from . import auth_db, licensing

try:
    import jwt as _pyjwt  # type: ignore

    _HAS_PYJWT = True
except ImportError:
    _pyjwt = None
    _HAS_PYJWT = False

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DEFAULT_AUTH_SECRET = "plenary-suite-dev-auth-secret-change-in-prod"
_DEFAULT_TOKEN_TTL = 86400 * 7  # 7 days


def _get_auth_secret() -> str:
    return (
        os.environ.get("PLENARY_AUTH_SECRET")
        or os.environ.get("JWT_SECRET")
        or _DEFAULT_AUTH_SECRET
    )


def _get_token_ttl() -> int:
    try:
        return int(os.environ.get("PLENARY_TOKEN_TTL_SECONDS", _DEFAULT_TOKEN_TTL))
    except ValueError:
        return _DEFAULT_TOKEN_TTL


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii"))


def create_access_token(user: dict[str, Any], expires_in: int | None = None) -> str:
    """Create a signed HS256 JWT for the given user dict."""
    now = int(time.time())
    ttl = expires_in if expires_in is not None else _get_token_ttl()
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user.get("role", "user"),
        "iat": now,
        "exp": now + int(ttl),
    }
    secret = _get_auth_secret()

    if _HAS_PYJWT:
        token = _pyjwt.encode(payload, secret, algorithm="HS256")
        return token if isinstance(token, str) else token.decode("utf-8")

    header_b64 = _b64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
    )
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(sig)}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify an HS256 JWT; returns claims dict or None if invalid/expired."""
    if not token or not isinstance(token, str):
        return None
    secret = _get_auth_secret()

    if _HAS_PYJWT:
        try:
            claims = _pyjwt.decode(token, secret, algorithms=["HS256"])
            return claims if isinstance(claims, dict) else None
        except Exception:
            return None

    parts = token.strip().split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        return None

    if not hmac.compare_digest(actual_sig, expected_sig):
        return None

    try:
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None

    if not isinstance(header, dict) or header.get("alg") != "HS256":
        return None
    if not isinstance(payload, dict):
        return None

    exp = payload.get("exp")
    if exp is not None and time.time() > float(exp):
        return None
    return payload


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def get_current_user_optional(request: Request) -> dict[str, Any] | None:
    """FastAPI dependency: extract Bearer token and return user dict (+ tier), or None."""
    auth_header = request.headers.get("authorization") or ""
    if not auth_header:
        return None
    parts = auth_header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    claims = decode_access_token(parts[1].strip())
    if not claims or "sub" not in claims:
        return None

    try:
        user_id = int(claims["sub"])
    except (TypeError, ValueError):
        return None

    user = auth_db.get_user_by_id(user_id)
    if user is None or not user.get("is_active"):
        return None

    user["tier"] = auth_db.get_user_tier(user["id"])
    return user


def get_current_user(user: dict[str, Any] | None = Depends(get_current_user_optional)) -> dict[str, Any]:
    """FastAPI dependency: require an authenticated user or raise 401."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=256)
    display_name: str = Field("", max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=256)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request):
    """Register a new user account and return an access token."""
    try:
        user = auth_db.create_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            tier="free",
            ip_address=_client_ip(request),
        )
    except ValueError as exc:
        msg = str(exc)
        code = status.HTTP_409_CONFLICT if "already registered" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from exc

    tier = auth_db.get_user_tier(user["id"])
    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "tier": tier,
    }


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    """Authenticate with email + password and return an access token."""
    user = auth_db.authenticate_user(
        email=payload.email,
        password=payload.password,
        ip_address=_client_ip(request),
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    tier = auth_db.get_user_tier(user["id"])
    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "tier": tier,
    }


@router.get("/me")
def me(user: dict[str, Any] = Depends(get_current_user)):
    """Return the currently authenticated user profile and active tier."""
    return {
        "user": user,
        "tier": user["tier"],
    }


@router.get("/entitlements")
def entitlements(user: dict[str, Any] | None = Depends(get_current_user_optional)):
    """Return translation and feature entitlements for the current user (or free tier)."""
    tier = user["tier"] if user is not None else "free"
    data = licensing.get_entitlements_for_tier(tier)
    data["authenticated"] = user is not None
    data["user_id"] = user["id"] if user is not None else None
    return data
