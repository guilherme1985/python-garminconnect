"""Garmin Connect singleton wrapper for the dashboard."""

from __future__ import annotations

import logging
import os
import threading
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garminconnect.cache import DiskCache, InMemoryCache

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client: Garmin | None = None
_login_error: str | None = None


def _build_client() -> Garmin:
    """Construct and authenticate a Garmin client.

    Tries existing tokens first; falls back to password login. MFA must
    be pre-handled (e.g. valid tokens cached on the mounted volume).
    """
    email = os.getenv("GARMIN_EMAIL") or os.getenv("EMAIL")
    password = os.getenv("GARMIN_PASSWORD") or os.getenv("PASSWORD")
    tokenstore = os.getenv("GARMINTOKENS", "/data/tokens")
    is_cn = os.getenv("GARMIN_IS_CN", "false").lower() == "true"
    login_timeout = float(os.getenv("GARMIN_LOGIN_TIMEOUT", "180"))

    Path(tokenstore).expanduser().mkdir(parents=True, exist_ok=True)

    if not email or not password:
        raise RuntimeError(
            "GARMIN_EMAIL/GARMIN_PASSWORD not configured (see .env)."
        )

    cache_dir = os.getenv("GARMIN_CACHE_DIR")
    cache: Any = None
    if cache_dir:
        try:
            cache = DiskCache(cache_dir)
        except Exception as exc:  # noqa: BLE001 — DiskCache failure must not crash app
            logger.warning("DiskCache(%s) failed (%s: %s) — falling back to memory",
                           cache_dir, type(exc).__name__, exc)
            cache = InMemoryCache()

    garmin = Garmin(
        email=email,
        password=password,
        is_cn=is_cn,
        login_timeout=login_timeout,
        cache=cache,
        prompt_mfa=lambda: (_ for _ in ()).throw(
            RuntimeError(
                "MFA required — generate tokens locally first with "
                "example.py and mount the token directory."
            )
        ),
    )
    garmin.login(tokenstore)
    logger.info("Garmin login OK — display_name=%s", garmin.display_name)
    return garmin


def get_client() -> Garmin:
    """Return the authenticated Garmin client (lazy init)."""
    global _client, _login_error
    with _lock:
        if _client is not None:
            return _client
        try:
            _client = _build_client()
            _login_error = None
            return _client
        except (
            GarminConnectAuthenticationError,
            GarminConnectConnectionError,
            GarminConnectTooManyRequestsError,
            RuntimeError,
        ) as exc:
            _login_error = f"{type(exc).__name__}: {exc}"
            logger.exception("Garmin login failed")
            raise


def login_error() -> str | None:
    """Return last login error message, if any."""
    return _login_error


def reset_client() -> None:
    """Drop the cached client (force re-login on next call)."""
    global _client
    with _lock:
        _client = None


# ----------------- helpers ------------------------------------------- #


def yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def safe_call(method_name: str, *args: Any, **kwargs: Any) -> tuple[Any, str | None]:
    """Call a method on the cached client; return (value, error_string)."""
    try:
        g = get_client()
        method = getattr(g, method_name)
        return method(*args, **kwargs), None
    except Exception as exc:  # noqa: BLE001 — surface any error to UI
        logger.exception("safe_call %s failed", method_name)
        return None, f"{type(exc).__name__}: {exc}"
