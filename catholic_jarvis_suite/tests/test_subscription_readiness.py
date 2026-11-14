"""Comprehensive tests for Plenary Suite subscription readiness:
auth, tiered entitlements, patristics, media, readiness probe, and thin shell.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

SUITE_DIR = Path(__file__).resolve().parents[1]
WEB_APP_DIR = SUITE_DIR.parents[1] / "web_app"
if str(SUITE_DIR) not in sys.path:
    sys.path.insert(0, str(SUITE_DIR))

from app import app  # noqa: E402
from modules import licensing  # noqa: E402

client = TestClient(app)


def test_health_ready():
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["plenary_sqlite"] is True


def test_patristics_migne_and_schaff():
    resp = client.get("/api/plenary/patristics?series=PL&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    assert all(item["series"] == "PL" for item in data["items"])

    q_resp = client.get("/api/plenary/patristics?q=Augustine&limit=5")
    assert q_resp.status_code == 200
    assert q_resp.json()["count"] >= 0


def test_media_endpoint():
    resp = client.get("/api/plenary/media")
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_auth_and_offline_license_key():
    email = f"scholar_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "StrongTestPassword123!", "display_name": "Test Scholar"},
    )
    assert reg.status_code in (200, 201)
    token = reg.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == email

    ent = client.get("/api/auth/entitlements", headers={"Authorization": f"Bearer {token}"})
    assert ent.status_code == 200
    assert ent.json()["tier"] == "free"

    plans = client.get("/api/billing/plans")
    assert plans.status_code == 200

    key = licensing.generate_license_key(subject=email, tier="scholar_pro", expires_in_days=30)
    ver = client.post("/api/billing/verify_license_key", json={"license_key": key})
    assert ver.status_code == 200
    assert ver.json()["valid"] is True
    assert ver.json()["tier"] == "scholar_pro"


def test_saas_entitlement_gating():
    prev = os.environ.get("PLENARY_SAAS_MODE")
    try:
        os.environ["PLENARY_SAAS_MODE"] = "1"
        denied = client.get("/api/plenary/chapter/gen/1?translations=nkjv")
        assert denied.status_code == 403

        allowed = client.get("/api/plenary/chapter/gen/1?translations=dra,vul")
        assert allowed.status_code == 200
    finally:
        if prev is None:
            os.environ.pop("PLENARY_SAAS_MODE", None)
        else:
            os.environ["PLENARY_SAAS_MODE"] = prev


def test_thin_shell_size():
    shell_path = WEB_APP_DIR / "plenary_logos_shell.html"
    assert shell_path.is_file(), f"Missing thin shell at {shell_path}"
    assert shell_path.stat().st_size < 1_000_000
