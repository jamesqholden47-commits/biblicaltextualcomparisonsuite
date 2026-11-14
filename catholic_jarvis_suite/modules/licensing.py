"""
licensing.py -- Tier entitlements, translation gating, and HMAC-SHA256 signed
offline license keys for Plenary Suite (web & Tauri/desktop offline mode).

Zero external dependencies: uses only Python stdlib.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

VALID_TIERS = ("free", "scholar_pro", "institutional")

FREE_TRANSLATIONS: frozenset[str] = frozenset(
    {
        "dra",
        "vul",
        "gr",
        "he",
        "kjv",
        "asv",
        "web",
        "webc",
        "ylt",
        "darby",
        "geneva",
        "bbe",
        "tyndale",
        "bsb",
        "cpdv",
        "lxx_en",
        "nova_vulg",
    }
)

SCHOLAR_PRO_ADDITIONS: frozenset[str] = frozenset(
    {
        "nkjv",
        "nabre",
        "rsv2ce",
        "net21",
        "ignatius",
    }
)

INSTITUTIONAL_ADDITIONS: frozenset[str] = frozenset(
    {
        "esv",
        "nrsv",
        "nrsvce",
        "nasb",
        "niv",
        "csb",
    }
)

TIER_ENTITLEMENTS: dict[str, frozenset[str]] = {
    "free": FREE_TRANSLATIONS,
    "scholar_pro": FREE_TRANSLATIONS | SCHOLAR_PRO_ADDITIONS,
    "institutional": FREE_TRANSLATIONS | SCHOLAR_PRO_ADDITIONS | INSTITUTIONAL_ADDITIONS,
}

_LICENSE_PREFIX = "PLENARY1"
_DEFAULT_LICENSE_SECRET = "plenary-suite-dev-license-secret-change-in-prod"


def _get_license_secret(secret: str | None = None) -> bytes:
    raw = (
        secret
        or os.environ.get("PLENARY_LICENSE_SECRET")
        or os.environ.get("PLENARY_AUTH_SECRET")
        or _DEFAULT_LICENSE_SECRET
    )
    return raw.encode("utf-8")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii"))


def normalize_tier(tier: str | None) -> str:
    t = (tier or "free").strip().lower()
    return t if t in TIER_ENTITLEMENTS else "free"


def is_translation_allowed(tier: str | None, tr_id: str | None) -> bool:
    """Return True if the given tier is entitled to access translation `tr_id`."""
    tr = (tr_id or "").strip().lower()
    if not tr:
        return False
    norm_tier = normalize_tier(tier)
    if norm_tier == "institutional":
        return True
    return tr in TIER_ENTITLEMENTS[norm_tier]


def get_entitlements_for_tier(tier: str | None) -> dict[str, Any]:
    """Return a JSON-serializable entitlement summary for `tier`."""
    norm_tier = normalize_tier(tier)
    return {
        "tier": norm_tier,
        "translations": sorted(TIER_ENTITLEMENTS[norm_tier]),
        "all_translations": norm_tier == "institutional",
        "offline_license": norm_tier in ("scholar_pro", "institutional"),
    }


def generate_license_key(
    subject: str,
    tier: str = "scholar_pro",
    expires_in_days: int | None = 365,
    org: str = "",
    secret: str | None = None,
    now: float | None = None,
) -> str:
    """Generate an HMAC-SHA256 signed offline license token (`PLENARY1.<payload>.<sig>`)."""
    norm_tier = (tier or "").strip().lower()
    if norm_tier not in VALID_TIERS:
        raise ValueError(f"Invalid tier: {tier}")
    if not subject or not str(subject).strip():
        raise ValueError("License subject must be non-empty")

    issued_at = int(now if now is not None else time.time())
    expires_at = (
        issued_at + int(expires_in_days) * 86400
        if expires_in_days is not None
        else None
    )

    payload = {
        "v": 1,
        "sub": str(subject).strip(),
        "tier": norm_tier,
        "org": (org or "").strip(),
        "iat": issued_at,
        "exp": expires_at,
        "jti": secrets.token_hex(8),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)

    signing_input = f"{_LICENSE_PREFIX}.{payload_b64}".encode("ascii")
    sig = hmac.new(_get_license_secret(secret), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{_LICENSE_PREFIX}.{payload_b64}.{sig_b64}"


def verify_license_key(
    token: str,
    secret: str | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Verify an offline license key and return its decoded claims & entitlements."""
    if not isinstance(token, str) or not token.strip():
        return {"valid": False, "error": "Empty license key"}

    parts = token.strip().split(".")
    if len(parts) != 3 or parts[0] != _LICENSE_PREFIX:
        return {"valid": False, "error": "Malformed license key format"}

    _, payload_b64, sig_b64 = parts
    signing_input = f"{_LICENSE_PREFIX}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(_get_license_secret(secret), signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        return {"valid": False, "error": "Invalid signature encoding"}

    if not hmac.compare_digest(actual_sig, expected_sig):
        return {"valid": False, "error": "Invalid license signature"}

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return {"valid": False, "error": "Corrupt license payload"}

    if not isinstance(payload, dict) or payload.get("tier") not in VALID_TIERS:
        return {"valid": False, "error": "Invalid license tier"}

    current_time = now if now is not None else time.time()
    exp = payload.get("exp")
    if exp is not None and current_time > float(exp):
        return {"valid": False, "error": "License key expired", "expired_at": exp}

    tier = payload["tier"]
    return {
        "valid": True,
        "subject": payload.get("sub"),
        "tier": tier,
        "org": payload.get("org", ""),
        "issued_at": payload.get("iat"),
        "expires_at": exp,
        "jti": payload.get("jti"),
        "entitlements": get_entitlements_for_tier(tier),
    }
