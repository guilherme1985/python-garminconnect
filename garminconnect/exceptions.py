"""Legacy exception module — re-exports from the formal hierarchy.

This module exists for backward compatibility. The canonical hierarchy
lives in :mod:`garminconnect.models.exceptions`. All names exported here
remain identical to the original flat structure used in previous releases.

For new code, prefer importing directly from the formal hierarchy:

    from garminconnect.models.exceptions import (
        GarminAuthError,
        GarminTransportError,
        GarminRateLimitError,
    )
"""

from .models.exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectInvalidFileFormatError,
    GarminConnectTooManyRequestsError,
)

__all__ = [
    "GarminConnectAuthenticationError",
    "GarminConnectConnectionError",
    "GarminConnectInvalidFileFormatError",
    "GarminConnectTooManyRequestsError",
]
