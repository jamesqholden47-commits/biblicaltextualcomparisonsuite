"""
rate_limit.py -- Sliding-window in-memory rate limiter, Starlette/FastAPI
middleware, and route dependency helper for Plenary Suite.

Zero external dependencies beyond Python stdlib and Starlette/FastAPI.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Callable, Iterable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

TIER_RATE_LIMITS: dict[str, tuple[int, float]] = {
    "free": (60, 60.0),
    "scholar_pro": (300, 60.0),
    "institutional": (1200, 60.0),
}


class RateLimiter:
    """Thread-safe sliding-window in-memory rate limiter."""

    def __init__(
        self,
        default_limit: int = 60,
        default_window_seconds: float = 60.0,
        max_keys: int = 10_000,
    ) -> None:
        self.default_limit = int(default_limit)
        self.default_window_seconds = float(default_window_seconds)
        self.max_keys = int(max_keys)
        self._buckets: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(
        self,
        key: str,
        limit: int | None = None,
        window_seconds: float | None = None,
        now: float | None = None,
    ) -> tuple[bool, dict[str, int | float]]:
        """Check whether `key` is within its sliding-window quota and record hit if allowed."""
        cap = self.default_limit if limit is None else int(limit)
        window = self.default_window_seconds if window_seconds is None else float(window_seconds)
        ts = time.monotonic() if now is None else float(now)
        cutoff = ts - window

        with self._lock:
            if len(self._buckets) >= self.max_keys and key not in self._buckets:
                self._prune_stale(cutoff)

            dq = self._buckets.get(key)
            if dq is None:
                dq = deque()
                self._buckets[key] = dq

            while dq and dq[0] <= cutoff:
                dq.popleft()

            if len(dq) < cap:
                dq.append(ts)
                remaining = cap - len(dq)
                reset_after = max(0.0, window - (ts - dq[0])) if dq else window
                return True, {
                    "limit": cap,
                    "remaining": remaining,
                    "reset_after": round(reset_after, 3),
                    "retry_after": 0,
                }

            retry_after = max(1, int(window - (ts - dq[0])) + 1) if dq else int(window)
            return False, {
                "limit": cap,
                "remaining": 0,
                "reset_after": round(max(0.0, window - (ts - dq[0])), 3) if dq else window,
                "retry_after": retry_after,
            }

    def reset(self, key: str | None = None) -> None:
        """Clear recorded timestamps for `key`, or all keys if `key` is None."""
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)

    def _prune_stale(self, cutoff: float) -> None:
        stale_keys = [k for k, dq in self._buckets.items() if not dq or dq[-1] <= cutoff]
        for k in stale_keys:
            del self._buckets[k]
        if len(self._buckets) >= self.max_keys:
            oldest_key = next(iter(self._buckets), None)
            if oldest_key is not None:
                del self._buckets[oldest_key]


def default_key_func(request: Request) -> str:
    """Identify caller by forwarded IP or client host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware applying a sliding-window RateLimiter to incoming HTTP requests."""

    def __init__(
        self,
        app,
        limiter: RateLimiter | None = None,
        limit: int = 60,
        window_seconds: float = 60.0,
        key_func: Callable[[Request], str] = default_key_func,
        exempt_paths: Iterable[str] = ("/health", "/api/billing/webhook"),
    ) -> None:
        super().__init__(app)
        self.limiter = limiter or RateLimiter(default_limit=limit, default_window_seconds=window_seconds)
        self.limit = int(limit)
        self.window_seconds = float(window_seconds)
        self.key_func = key_func
        self.exempt_paths = set(exempt_paths)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        key = self.key_func(request)
        allowed, meta = self.limiter.allow(key, limit=self.limit, window_seconds=self.window_seconds)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded", "retry_after": meta["retry_after"]},
                headers={
                    "Retry-After": str(meta["retry_after"]),
                    "X-RateLimit-Limit": str(meta["limit"]),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(meta["limit"])
        response.headers["X-RateLimit-Remaining"] = str(meta["remaining"])
        return response


def rate_limit_dependency(
    limit: int = 60,
    window_seconds: float = 60.0,
    limiter: RateLimiter | None = None,
    key_func: Callable[[Request], str] = default_key_func,
):
    """Return a FastAPI dependency that enforces a sliding-window rate limit."""
    rl = limiter or RateLimiter(default_limit=limit, default_window_seconds=window_seconds)

    async def _check_rate_limit(request: Request) -> dict[str, int | float]:
        key = f"{request.url.path}:{key_func(request)}"
        allowed, meta = rl.allow(key, limit=limit, window_seconds=window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(meta["retry_after"])},
            )
        return meta

    return _check_rate_limit
