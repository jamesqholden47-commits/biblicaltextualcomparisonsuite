"""
auth_db.py -- SQLite persistence for Plenary Suite authentication, subscriptions,
and audit logging.

Manages `data/auth.sqlite` with three tables:
  - users
  - subscriptions
  - audit_log

Uses only Python standard library (`sqlite3`, `hashlib`, `hmac`, `secrets`,
`base64`, `json`, `os`, `threading`, `time`).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from typing import Any

from .paths_config import DATA_DIR

DEFAULT_DB_PATH = os.environ.get(
    "PLENARY_AUTH_DB",
    os.path.join(DATA_DIR, "auth.sqlite"),
)

VALID_TIERS = ("free", "scholar_pro", "institutional")
TIER_RANK = {"free": 0, "scholar_pro": 1, "institutional": 2}
ACTIVE_SUBSCRIPTION_STATUSES = ("active", "trialing")

_PBKDF2_ITERATIONS = 200_000
_INIT_LOCK = threading.Lock()
_INITIALIZED_PATHS: set[str] = set()


def _resolve_db_path(db_path: str | None = None) -> str:
    return os.path.abspath(db_path or DEFAULT_DB_PATH)


def init_db(db_path: str | None = None) -> str:
    """Create the SQLite database file and schema if they do not exist."""
    resolved = _resolve_db_path(db_path)
    parent = os.path.dirname(resolved)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(resolved, timeout=15.0)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                tier TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                provider TEXT NOT NULL DEFAULT 'manual',
                provider_customer_id TEXT,
                provider_subscription_id TEXT,
                current_period_end REAL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
                ON subscriptions(user_id);

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '{}',
                ip_address TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_audit_log_user_created
                ON audit_log(user_id, created_at);
            """
        )
        conn.commit()
    finally:
        conn.close()

    with _INIT_LOCK:
        _INITIALIZED_PATHS.add(resolved)
    return resolved


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a configured SQLite connection, initializing schema on first use."""
    resolved = _resolve_db_path(db_path)
    with _INIT_LOCK:
        needs_init = resolved not in _INITIALIZED_PATHS
    if needs_init:
        init_db(resolved)

    conn = sqlite3.connect(resolved, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password: str, iterations: int = _PBKDF2_ITERATIONS) -> str:
    """Hash a plaintext password with PBKDF2-HMAC-SHA256 and a per-user salt."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
    dk_b64 = base64.urlsafe_b64encode(dk).decode("ascii")
    return f"pbkdf2_sha256${iterations}${salt_b64}${dk_b64}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2-HMAC-SHA256 hash."""
    if not password or not stored_hash:
        return False
    try:
        scheme, iter_str, salt_b64, dk_b64 = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(dk_b64.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _row_to_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def log_audit(
    action: str,
    user_id: int | None = None,
    detail: dict[str, Any] | str | None = None,
    ip_address: str = "",
    db_path: str | None = None,
) -> None:
    """Insert an entry into the audit_log table."""
    if isinstance(detail, dict):
        detail_str = json.dumps(detail, sort_keys=True)
    elif detail is None:
        detail_str = "{}"
    else:
        detail_str = str(detail)

    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO audit_log (user_id, action, detail, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, action, detail_str, ip_address or "", time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def create_user(
    email: str,
    password: str,
    display_name: str = "",
    tier: str = "free",
    ip_address: str = "",
    db_path: str | None = None,
) -> dict[str, Any]:
    """Create a new user and initial subscription row, returning public user fields."""
    norm_email = _normalize_email(email)
    if not norm_email or "@" not in norm_email:
        raise ValueError("A valid email address is required")
    if tier not in VALID_TIERS:
        raise ValueError(f"Invalid tier: {tier}")

    pw_hash = hash_password(password)
    now = time.time()

    conn = get_connection(db_path)
    try:
        try:
            cur = conn.execute(
                """
                INSERT INTO users (email, password_hash, display_name, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 'user', 1, ?, ?)
                """,
                (norm_email, pw_hash, (display_name or "").strip(), now, now),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Email is already registered") from exc

        user_id = cur.lastrowid
        conn.execute(
            """
            INSERT INTO subscriptions (user_id, tier, status, provider, created_at, updated_at)
            VALUES (?, ?, 'active', 'manual', ?, ?)
            """,
            (user_id, tier, now, now),
        )
        conn.execute(
            """
            INSERT INTO audit_log (user_id, action, detail, ip_address, created_at)
            VALUES (?, 'user.register', ?, ?, ?)
            """,
            (user_id, json.dumps({"email": norm_email, "tier": tier}), ip_address or "", now),
        )
        conn.commit()

        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = _row_to_user(row)
        assert user is not None
        return user
    finally:
        conn.close()


def get_user_by_id(user_id: int, db_path: str | None = None) -> dict[str, Any] | None:
    """Fetch a user by primary key (without password_hash)."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def get_user_by_email(email: str, db_path: str | None = None) -> dict[str, Any] | None:
    """Fetch a user by normalized email (without password_hash)."""
    norm_email = _normalize_email(email)
    if not norm_email:
        return None
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (norm_email,)).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def authenticate_user(
    email: str,
    password: str,
    ip_address: str = "",
    db_path: str | None = None,
) -> dict[str, Any] | None:
    """Verify email/password and record login outcome in audit_log."""
    norm_email = _normalize_email(email)
    if not norm_email or not password:
        return None

    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (norm_email,)).fetchone()
        now = time.time()
        if row is None or not row["is_active"] or not verify_password(password, row["password_hash"]):
            uid = row["id"] if row is not None else None
            conn.execute(
                """
                INSERT INTO audit_log (user_id, action, detail, ip_address, created_at)
                VALUES (?, 'user.login_failed', ?, ?, ?)
                """,
                (uid, json.dumps({"email": norm_email}), ip_address or "", now),
            )
            conn.commit()
            return None

        conn.execute(
            """
            INSERT INTO audit_log (user_id, action, detail, ip_address, created_at)
            VALUES (?, 'user.login', ?, ?, ?)
            """,
            (row["id"], json.dumps({"email": norm_email}), ip_address or "", now),
        )
        conn.commit()
        return _row_to_user(row)
    finally:
        conn.close()


def get_user_tier(user_id: int | None, db_path: str | None = None) -> str:
    """Return the user's highest active tier: 'free', 'scholar_pro', or 'institutional'."""
    if user_id is None:
        return "free"

    now = time.time()
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT tier, status, current_period_end
            FROM subscriptions
            WHERE user_id = ? AND status IN ('active', 'trialing')
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    best_tier = "free"
    for row in rows:
        period_end = row["current_period_end"]
        if period_end is not None and period_end <= now:
            continue
        tier = row["tier"]
        if tier in TIER_RANK and TIER_RANK[tier] > TIER_RANK[best_tier]:
            best_tier = tier
    return best_tier


def set_user_subscription(
    user_id: int,
    tier: str,
    status: str = "active",
    provider: str = "manual",
    provider_customer_id: str | None = None,
    provider_subscription_id: str | None = None,
    current_period_end: float | None = None,
    ip_address: str = "",
    db_path: str | None = None,
) -> dict[str, Any]:
    """Create or update a user's subscription and record an audit_log entry."""
    if tier not in VALID_TIERS:
        raise ValueError(f"Invalid tier: {tier}")

    now = time.time()
    conn = get_connection(db_path)
    try:
        existing = conn.execute(
            """
            SELECT id FROM subscriptions
            WHERE user_id = ? AND provider = ?
            ORDER BY updated_at DESC LIMIT 1
            """,
            (user_id, provider),
        ).fetchone()

        if existing is not None:
            sub_id = existing["id"]
            conn.execute(
                """
                UPDATE subscriptions
                SET tier = ?, status = ?, provider_customer_id = COALESCE(?, provider_customer_id),
                    provider_subscription_id = COALESCE(?, provider_subscription_id),
                    current_period_end = ?, updated_at = ?
                WHERE id = ?
                """,
                (tier, status, provider_customer_id, provider_subscription_id, current_period_end, now, sub_id),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO subscriptions (
                    user_id, tier, status, provider,
                    provider_customer_id, provider_subscription_id,
                    current_period_end, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    tier,
                    status,
                    provider,
                    provider_customer_id,
                    provider_subscription_id,
                    current_period_end,
                    now,
                    now,
                ),
            )
            sub_id = cur.lastrowid

        conn.execute(
            """
            INSERT INTO audit_log (user_id, action, detail, ip_address, created_at)
            VALUES (?, 'subscription.updated', ?, ?, ?)
            """,
            (
                user_id,
                json.dumps({"tier": tier, "status": status, "provider": provider}),
                ip_address or "",
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()
