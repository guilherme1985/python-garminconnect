"""In-memory cache backend (F5-02)."""

from __future__ import annotations

import threading
import time
from typing import Any

from .backend import MISSING


class InMemoryCache:
    """Thread-safe dict-backed cache with per-entry TTL.

    Suitable for short-lived processes (CLI, scripts). For persistence
    across runs use :class:`DiskCache`.
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = MISSING) -> Any:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return default
            expires_at, value = entry
            if expires_at < time.time():
                self._data.pop(key, None)
                return default
            return value

    def set(self, key: str, value: Any, ttl_s: float) -> None:
        with self._lock:
            self._data[key] = (time.time() + ttl_s, value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
