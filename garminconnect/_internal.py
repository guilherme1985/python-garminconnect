"""Internal helpers shared between the legacy __init__.py and domain mixins.

This module exists to break circular imports during the incremental refactor
to the domain/* mixin architecture. Public consumers should not import from
here directly — these are implementation details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

    import requests

VALID_WEIGHT_UNITS = {"kg", "lbs"}


def fmt_ts(dt: datetime) -> str:
    """Format a datetime to ms-precision ISO string expected by the API."""
    return dt.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def validate_json_exists(response: requests.Response) -> dict[str, Any] | None:
    """Return parsed JSON, or None for HTTP 204 (No Content) responses."""
    if response.status_code == 204:
        return None
    return response.json()


# Backwards-compatible aliases (used by legacy code in __init__.py)
_fmt_ts = fmt_ts
_validate_json_exists = validate_json_exists
