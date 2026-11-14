"""
billing_routes.py -- FastAPI billing, Stripe-compatible checkout/webhook skeleton,
and offline license key verification routes for Plenary Suite.

Endpoints:
  GET  /api/billing/plans
  POST /api/billing/checkout_session
  POST /api/billing/webhook
  POST /api/billing/verify_license_key
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from . import auth_db, licensing
from .auth_routes import get_current_user_optional

router = APIRouter(prefix="/api/billing", tags=["billing"])

PLANS: list[dict[str, Any]] = [
    {
        "id": "free",
        "name": "Free",
        "price_monthly_cents": 0,
        "price_yearly_cents": 0,
        "translations": sorted(licensing.TIER_ENTITLEMENTS["free"]),
        "offline_license": False,
        "rate_limit_rpm": 60,
    },
    {
        "id": "scholar_pro",
        "name": "Scholar Pro",
        "price_monthly_cents": 900,
        "price_yearly_cents": 9000,
        "translations": sorted(licensing.TIER_ENTITLEMENTS["scholar_pro"]),
        "offline_license": True,
        "rate_limit_rpm": 300,
    },
    {
        "id": "institutional",
        "name": "Institutional",
        "price_monthly_cents": 4900,
        "price_yearly_cents": 49000,
        "translations": sorted(licensing.TIER_ENTITLEMENTS["institutional"]),
        "all_translations": True,
        "offline_license": True,
        "rate_limit_rpm": 1200,
    },
]


class CheckoutSessionRequest(BaseModel):
    tier: str = Field(..., description="Target tier: scholar_pro or institutional")
    interval: str = Field("monthly", description="monthly or yearly")
    success_url: str = Field("https://plenarysuite.local/billing/success")
    cancel_url: str = Field("https://plenarysuite.local/billing/cancel")


class VerifyLicenseRequest(BaseModel):
    license_key: str = Field(..., min_length=1)


def _verify_stripe_signature(payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    """Verify Stripe-Signature header (`t=<ts>,v1=<hex>`) using HMAC-SHA256."""
    if not sig_header or not secret:
        return False

    timestamp = None
    v1_sigs: list[str] = []
    for part in sig_header.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k == "t":
            timestamp = v
        elif k == "v1":
            v1_sigs.append(v)

    if not timestamp or not v1_sigs:
        return False

    try:
        ts_int = int(timestamp)
    except ValueError:
        return False

    if tolerance > 0 and abs(time.time() - ts_int) > tolerance:
        return False

    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in v1_sigs)


@router.get("/plans")
def list_plans():
    """Return available Plenary Suite subscription plans and entitlements."""
    return {"plans": PLANS, "currency": "usd"}


@router.post("/checkout_session")
def create_checkout_session(
    payload: CheckoutSessionRequest,
    user: dict[str, Any] | None = Depends(get_current_user_optional),
):
    """Create a Stripe-compatible checkout session skeleton."""
    tier = payload.tier.strip().lower()
    if tier not in ("scholar_pro", "institutional"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout is only available for 'scholar_pro' or 'institutional' tiers",
        )
    interval = payload.interval.strip().lower()
    if interval not in ("monthly", "yearly"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interval must be 'monthly' or 'yearly'",
        )

    session_id = f"cs_test_{secrets.token_hex(12)}"
    return {
        "id": session_id,
        "object": "checkout.session",
        "mode": "subscription",
        "status": "open",
        "tier": tier,
        "interval": interval,
        "client_reference_id": str(user["id"]) if user else None,
        "customer_email": user["email"] if user else None,
        "success_url": payload.success_url,
        "cancel_url": payload.cancel_url,
        "url": f"https://checkout.stripe.com/pay/{session_id}",
        "livemode": False,
        "skeleton": True,
    }


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events with optional HMAC signature verification."""
    body = await request.body()
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
    if webhook_secret:
        sig_header = request.headers.get("stripe-signature", "")
        if not _verify_stripe_signature(body, sig_header, webhook_secret):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Stripe webhook signature",
            )

    try:
        event = json.loads(body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc

    if not isinstance(event, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event must be a JSON object")

    event_type = str(event.get("type") or "")
    obj = (event.get("data") or {}).get("object") or {}
    metadata = obj.get("metadata") or {}

    raw_user_id = obj.get("client_reference_id") or metadata.get("user_id")
    user_id: int | None = None
    if raw_user_id is not None:
        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError):
            user_id = None

    tier = str(metadata.get("tier") or "scholar_pro").strip().lower()
    if tier not in licensing.VALID_TIERS:
        tier = "scholar_pro"

    updated = False
    if user_id is not None and auth_db.get_user_by_id(user_id) is not None:
        if event_type in ("checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"):
            sub_status = str(obj.get("status") or "active")
            if event_type == "checkout.session.completed":
                sub_status = "active"
            auth_db.set_user_subscription(
                user_id=user_id,
                tier=tier,
                status=sub_status,
                provider="stripe",
                provider_customer_id=obj.get("customer"),
                provider_subscription_id=obj.get("subscription") or obj.get("id"),
                current_period_end=obj.get("current_period_end"),
            )
            updated = True
        elif event_type == "customer.subscription.deleted":
            auth_db.set_user_subscription(
                user_id=user_id,
                tier="free",
                status="canceled",
                provider="stripe",
                provider_customer_id=obj.get("customer"),
                provider_subscription_id=obj.get("id"),
            )
            updated = True

    auth_db.log_audit(
        action="billing.webhook",
        user_id=user_id,
        detail={"event_type": event_type, "updated": updated},
    )
    return {"received": True, "event_type": event_type, "updated": updated}


@router.post("/verify_license_key")
def verify_license_key_route(payload: VerifyLicenseRequest):
    """Verify an HMAC-SHA256 signed offline license key."""
    return licensing.verify_license_key(payload.license_key)
