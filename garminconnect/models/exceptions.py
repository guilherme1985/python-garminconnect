"""Formal exception hierarchy for Garmin Connect.

This module provides a typed exception hierarchy that replaces the original
flat exception structure. It maintains full backward compatibility through
aliases for the legacy exception names.

New hierarchy:

    GarminConnectError (base)
    ├── GarminAuthError              (authentication failures)
    │   ├── GarminCredentialsError   (invalid email/password)
    │   └── GarminMFARequired        (MFA challenge needed)
    ├── GarminTransportError         (HTTP / network failures)
    │   ├── GarminRateLimitError     (429)
    │   └── GarminServerError        (5xx)
    ├── GarminValidationError        (invalid input parameters)
    ├── GarminTokenError             (malformed / expired tokens)
    ├── GarminCacheError             (cache backend failures)
    └── GarminInvalidFileFormatError (invalid file upload format)

Legacy aliases (kept for backward compatibility):
    GarminConnectConnectionError      → GarminTransportError
    GarminConnectAuthenticationError  → GarminAuthError
    GarminConnectTooManyRequestsError → GarminRateLimitError
    GarminConnectInvalidFileFormatError → GarminInvalidFileFormatError
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests


class GarminConnectError(Exception):
    """Base exception for all Garmin Connect errors.

    Attributes:
        message: Human-readable error description.
        suggestion: Optional hint or link to docs/issues for resolution.

    """

    def __init__(
        self,
        message: str = "",
        *,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion

    def __str__(self) -> str:
        if self.suggestion:
            return f"{self.message}\nSuggestion: {self.suggestion}"
        return self.message


# ---------------------------------------------------------------------------
# Authentication errors
# ---------------------------------------------------------------------------


class GarminAuthError(GarminConnectError):
    """Authentication failed.

    Attributes:
        strategy: Name of the login strategy that failed (e.g. 'mobile+cffi').
        requires_mfa: True when failure was due to MFA requirement.

    """

    def __init__(
        self,
        message: str = "",
        *,
        strategy: str | None = None,
        requires_mfa: bool = False,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, suggestion=suggestion)
        self.strategy = strategy
        self.requires_mfa = requires_mfa


class GarminCredentialsError(GarminAuthError):
    """Invalid email or password."""


class GarminMFARequired(GarminAuthError):
    """MFA challenge required to complete login.

    Attributes:
        method: MFA method requested ('totp', 'email', etc).

    """

    def __init__(
        self,
        message: str = "MFA required",
        *,
        method: str | None = None,
        strategy: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(
            message,
            strategy=strategy,
            requires_mfa=True,
            suggestion=suggestion,
        )
        self.method = method


# ---------------------------------------------------------------------------
# Transport / HTTP errors
# ---------------------------------------------------------------------------


class GarminTransportError(GarminConnectError):
    """HTTP or network-level failure.

    Attributes:
        status_code: HTTP status code, if available.
        response: Underlying requests.Response object, if available.
        is_retryable: True if the error is transient (5xx, network).

    """

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int | None = None,
        response: requests.Response | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, suggestion=suggestion)
        self.status_code = status_code
        self.response = response

    @property
    def is_retryable(self) -> bool:
        """Whether this error represents a transient failure worth retrying."""
        if self.status_code is None:
            return True  # Network-level errors are typically retryable
        return 500 <= self.status_code < 600


class GarminRateLimitError(GarminTransportError):
    """Rate limit exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from Retry-After
            header if present.

    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int | None = None,
        response: requests.Response | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=429,
            response=response,
            suggestion=suggestion,
        )
        self.retry_after = retry_after

    @property
    def is_retryable(self) -> bool:
        return False  # 429 fails fast — caller should back off explicitly


class GarminServerError(GarminTransportError):
    """Server-side error (HTTP 5xx)."""

    @property
    def is_retryable(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Validation / data errors
# ---------------------------------------------------------------------------


class GarminValidationError(GarminConnectError):
    """Input parameter failed validation.

    Attributes:
        param_name: Name of the parameter that failed validation.

    """

    def __init__(
        self,
        message: str = "",
        *,
        param_name: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message, suggestion=suggestion)
        self.param_name = param_name


class GarminTokenError(GarminConnectError):
    """Token store error — malformed JSON, base64, expired, etc."""


class GarminCacheError(GarminConnectError):
    """Cache backend error (read/write failure, corruption)."""


class GarminInvalidFileFormatError(GarminConnectError):
    """Invalid file format provided for upload."""


# ---------------------------------------------------------------------------
# Backward-compatible aliases (legacy names from garminconnect/exceptions.py)
# ---------------------------------------------------------------------------

# These aliases ensure that all existing user code keeps working:
#   except GarminConnectConnectionError       → still catches transport errors
#   except GarminConnectAuthenticationError   → still catches auth errors
#   except GarminConnectTooManyRequestsError  → still catches rate limits
GarminConnectConnectionError = GarminTransportError
GarminConnectAuthenticationError = GarminAuthError
GarminConnectTooManyRequestsError = GarminRateLimitError
GarminConnectInvalidFileFormatError = GarminInvalidFileFormatError


__all__ = [
    # New hierarchy
    "GarminConnectError",
    "GarminAuthError",
    "GarminCredentialsError",
    "GarminMFARequired",
    "GarminTransportError",
    "GarminRateLimitError",
    "GarminServerError",
    "GarminValidationError",
    "GarminTokenError",
    "GarminCacheError",
    "GarminInvalidFileFormatError",
    # Legacy aliases
    "GarminConnectConnectionError",
    "GarminConnectAuthenticationError",
    "GarminConnectTooManyRequestsError",
    "GarminConnectInvalidFileFormatError",
]
