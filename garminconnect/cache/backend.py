"""Cache backend protocol (F5-02)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

_SENTINEL = object()


@runtime_checkable
class CacheBackend(Protocol):
    """Minimal cache contract used by Garmin.connectapi.

    Implementations decide their own storage (RAM, SQLite, Redis, etc.)
    but must honour a TTL in seconds passed at ``set`` time.
    """

    def get(self, key: str, default: Any = _SENTINEL) -> Any:
        """Return the cached value or ``default`` (defaults to the sentinel
        meaning "missing"). Expired entries count as missing."""
        ...

    def set(self, key: str, value: Any, ttl_s: float) -> None:
        """Store ``value`` under ``key`` for ``ttl_s`` seconds."""
        ...

    def delete(self, key: str) -> None:
        """Remove ``key`` from the cache (no-op if missing)."""
        ...

    def clear(self) -> None:
        """Drop every entry."""
        ...


MISSING = _SENTINEL
