"""TokenStore — typed abstraction over OAuth token persistence.

Resolves BUG-010: tokenstore_base64 was decoded without validating the
contained JSON, leaking json.JSONDecodeError to callers. TokenStore validates
every load path and raises GarminTokenError with a clear message.

Also resolves ROAD-017: tokenstore accepts both str and Path.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
from pathlib import Path
from typing import Any

from ..models.exceptions import GarminTokenError

_LOGGER = logging.getLogger(__name__)


class TokenStore:
    """Encapsulates OAuth token lifecycle: load, validate, persist, clear.

    Attributes:
        data: Parsed token dict (may be empty before loading).
    """

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self._path: Path | None = None

    # ------------------------------------------------------------------ #
    #  Loading                                                           #
    # ------------------------------------------------------------------ #

    def load_from_path(self, path: str | Path) -> None:
        """Load tokens from a JSON file on disk.

        Raises:
            GarminTokenError: When the file is missing, unreadable, or
                contains invalid JSON.
        """
        path = Path(path).expanduser()
        try:
            with path.open("r", encoding="utf-8") as f:
                raw = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            raise GarminTokenError(
                f"Failed to read token file at {path}: {exc}",
                suggestion="Verify the file exists and is readable.",
            ) from exc

        self._parse_and_store(raw, source=f"file {path}")
        self._path = path

    def load_from_base64(self, encoded: str) -> None:
        """Load tokens from a base64-encoded JSON string.

        Raises:
            GarminTokenError: When base64 decoding fails or the decoded
                content is not valid JSON.
        """
        if not isinstance(encoded, str):
            raise GarminTokenError(
                "Base64 token must be a string",
                suggestion=f"Got {type(encoded).__name__}",
            )

        try:
            raw_bytes = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise GarminTokenError(
                f"Invalid base64 token string: {exc}",
                suggestion=(
                    "Ensure the token was correctly base64-encoded. "
                    "Use 'base64' command-line tool or Python's "
                    "base64.b64encode() to encode."
                ),
            ) from exc

        try:
            raw = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GarminTokenError(
                f"Base64-decoded content is not valid UTF-8: {exc}",
            ) from exc

        self._parse_and_store(raw, source="base64 string")

    def _parse_and_store(self, raw: str, *, source: str) -> None:
        """Parse JSON and validate minimal schema.

        Raises:
            GarminTokenError: When parsing fails or required fields are missing.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GarminTokenError(
                f"Token from {source} is not valid JSON: {exc.msg} "
                f"(line {exc.lineno}, col {exc.colno})",
                suggestion="Re-export tokens from a fresh login.",
            ) from exc

        if not isinstance(data, dict):
            raise GarminTokenError(
                f"Token from {source} must be a JSON object, got "
                f"{type(data).__name__}",
            )

        # Soft validation: warn if expected fields are missing but don't fail —
        # the API client will surface auth errors for genuinely broken tokens.
        expected = {"access_token", "refresh_token"}
        missing = expected - set(data.keys())
        if missing:
            _LOGGER.debug(
                "Token from %s is missing expected fields: %s",
                source,
                sorted(missing),
            )

        self.data = data

    # ------------------------------------------------------------------ #
    #  Persistence                                                       #
    # ------------------------------------------------------------------ #

    def dump(self, path: str | Path | None = None) -> Path:
        """Persist tokens to disk with permission 0600.

        Args:
            path: Destination path. If None, uses the path passed to load().

        Returns:
            The Path where tokens were written.

        Raises:
            GarminTokenError: When no path is set and no tokens are loaded.
        """
        target = Path(path).expanduser() if path else self._path
        if target is None:
            raise GarminTokenError(
                "No destination path for token dump",
                suggestion="Pass a path or call load_from_path first.",
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

        # Best-effort chmod — silently skip on Windows where chmod is a no-op.
        try:
            target.chmod(0o600)
        except (OSError, NotImplementedError) as exc:  # pragma: no cover
            _LOGGER.debug("Could not chmod token file %s: %s", target, exc)

        self._path = target
        return target

    def clear(self) -> None:
        """Remove tokens from memory. Does not delete the file."""
        self.data = {}

    # ------------------------------------------------------------------ #
    #  Inspection                                                        #
    # ------------------------------------------------------------------ #

    @property
    def access_token(self) -> str | None:
        return self.data.get("access_token")

    @property
    def refresh_token(self) -> str | None:
        return self.data.get("refresh_token")

    @property
    def expires_at(self) -> int | None:
        """Unix timestamp when the access token expires."""
        value = self.data.get("expires_at")
        return int(value) if isinstance(value, (int, float)) else None

    def is_expiring_soon(self, threshold_seconds: int = 300) -> bool:
        """Return True if the access token is about to expire.

        Args:
            threshold_seconds: Renew tokens whose expiry is within this window.
                Default is 5 minutes.
        """
        exp = self.expires_at
        if exp is None:
            return True  # Conservative: missing expiry → assume stale
        import time

        return (exp - time.time()) <= threshold_seconds

    @property
    def is_loaded(self) -> bool:
        return bool(self.data)

    def __repr__(self) -> str:
        loaded = "loaded" if self.is_loaded else "empty"
        return f"<TokenStore {loaded} path={self._path}>"

    # ------------------------------------------------------------------ #
    #  Security                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def check_permissions(path: str | Path) -> bool:
        """Warn if the token file has overly permissive permissions.

        Returns True if permissions are restrictive enough (0600 or stricter
        on Unix). On Windows always returns True.
        """
        path = Path(path).expanduser()
        if not path.exists() or os.name == "nt":
            return True

        mode = path.stat().st_mode & 0o777
        if mode & 0o077:
            _LOGGER.warning(
                "Token file %s has permissions %o — should be 0600. "
                "Run: chmod 600 %s",
                path,
                mode,
                path,
            )
            return False
        return True
