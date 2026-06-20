"""Disk-backed cache using SQLite (F5-02).

No external dependencies — pure stdlib (sqlite3 + pickle). For higher
throughput swap in `diskcache` or `aiocache` later.
"""

from __future__ import annotations

import pickle
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from .backend import MISSING


_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    key        TEXT PRIMARY KEY,
    expires_at REAL NOT NULL,
    value      BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_expires ON entries(expires_at);
"""


class DiskCache:
    """Persistent SQLite cache. Thread-safe; one DB connection per thread."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()
        self._path.mkdir(parents=True, exist_ok=True)
        self._db = self._path / "cache.sqlite3"
        self._local = threading.local()
        self._init_lock = threading.Lock()
        with self._init_lock:
            with self._conn() as c:
                c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._db, timeout=5, isolation_level=None)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return conn

    def get(self, key: str, default: Any = MISSING) -> Any:
        row = self._conn().execute(
            "SELECT expires_at, value FROM entries WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return default
        expires_at, blob = row
        if expires_at < time.time():
            self.delete(key)
            return default
        try:
            return pickle.loads(blob)
        except (pickle.UnpicklingError, EOFError, AttributeError):
            self.delete(key)
            return default

    def set(self, key: str, value: Any, ttl_s: float) -> None:
        try:
            blob = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except (pickle.PicklingError, TypeError):
            return  # unserialisable; skip silently
        self._conn().execute(
            "INSERT OR REPLACE INTO entries (key, expires_at, value) VALUES (?, ?, ?)",
            (key, time.time() + ttl_s, blob),
        )

    def delete(self, key: str) -> None:
        self._conn().execute("DELETE FROM entries WHERE key = ?", (key,))

    def clear(self) -> None:
        self._conn().execute("DELETE FROM entries")

    def prune(self) -> int:
        """Delete expired entries; returns number deleted."""
        cur = self._conn().execute(
            "DELETE FROM entries WHERE expires_at < ?", (time.time(),)
        )
        return cur.rowcount

    def __len__(self) -> int:
        return self._conn().execute("SELECT COUNT(*) FROM entries").fetchone()[0]
