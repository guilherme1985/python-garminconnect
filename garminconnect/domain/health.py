"""Health & daily summary domain methods.

Provides the HealthMixin class with methods for daily health stats, heart rate,
steps, sleep, and other wellness metrics.

This mixin assumes the host class provides:
    - self.connectapi(url, **kwargs)
    - self._require_display_name()
    - self.garmin_connect_daily_summary_url
    - self.garmin_connect_user_summary_chart
    - self.garmin_connect_heartrates_daily_url
"""

from __future__ import annotations

import logging
from typing import Any

from ..models.exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
)
from ..validation.validators import validate_date_format

logger = logging.getLogger(__name__)


class HealthMixin:
    """Mixin providing daily health and wellness API methods.

    All methods in this mixin require an authenticated session and a populated
    display name (set via login() / _load_profile_and_settings()).
    """

    # Type hints for attributes that exist on the host class. Declared here
    # as class-level Any so type checkers don't complain when the mixin is
    # used standalone. The host class (Garmin) populates these via __init__.
    connectapi: Any
    display_name: str | None
    garmin_connect_daily_summary_url: str
    garmin_connect_user_summary_chart: str
    garmin_connect_heartrates_daily_url: str

    def _require_display_name(self) -> str:
        """Return the populated display name or raise (provided by host)."""
        # Host class must implement this; this stub exists only for typing.
        raise NotImplementedError("Host class must implement _require_display_name")

    # ------------------------------------------------------------------ #
    #  Identity helpers                                                  #
    # ------------------------------------------------------------------ #

    def get_full_name(self) -> str | None:
        """Return user's full name."""
        return getattr(self, "full_name", None)

    def get_unit_system(self) -> str | None:
        """Return user's preferred unit system ('metric' or 'statute')."""
        return getattr(self, "unit_system", None)

    # ------------------------------------------------------------------ #
    #  Daily summary                                                     #
    # ------------------------------------------------------------------ #

    def get_stats(self, cdate: str) -> dict[str, Any]:
        """Return user activity summary for 'cdate' (YYYY-MM-DD).

        Alias for :meth:`get_user_summary` — kept for backward compatibility
        with code that predates the renaming.
        """
        cdate = validate_date_format(cdate, "cdate")
        return self.get_user_summary(cdate)

    def get_user_summary(self, cdate: str) -> dict[str, Any]:
        """Return user activity summary for 'cdate' (YYYY-MM-DD).

        Args:
            cdate: Date string in 'YYYY-MM-DD' format.

        Returns:
            Dict with totalKilocalories, activeKilocalories, totalSteps, etc.

        Raises:
            GarminConnectConnectionError: When the server returns no data.
            GarminConnectAuthenticationError: When the profile is privacy-protected.
            ValueError: When cdate is malformed.

        """
        cdate = validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_daily_summary_url}/{self._require_display_name()}"
        params = {"calendarDate": cdate}
        logger.debug("Requesting user summary")

        response = self.connectapi(url, params=params)

        if not response:
            raise GarminConnectConnectionError("No data received from server")

        if response.get("privacyProtected") is True:
            raise GarminConnectAuthenticationError("Authentication error")

        return response

    def get_steps_data(self, cdate: str) -> list[dict[str, Any]]:
        """Fetch intra-day steps data for 'cdate' (YYYY-MM-DD).

        Args:
            cdate: Date string in 'YYYY-MM-DD' format.

        Returns:
            List of intra-day step records. Empty list when no data is available.

        """
        cdate = validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_user_summary_chart}/{self._require_display_name()}"
        params = {"date": cdate}
        logger.debug("Requesting steps data")

        response = self.connectapi(url, params=params)

        if response is None:
            logger.warning("No steps data received")
            return []

        return response

    # ------------------------------------------------------------------ #
    #  Heart rate                                                        #
    # ------------------------------------------------------------------ #

    def get_heart_rates(self, cdate: str) -> dict[str, Any]:
        """Fetch available heart rates data 'cDate' format 'YYYY-MM-DD'.

        Args:
            cdate: Date string in 'YYYY-MM-DD' format.

        Returns:
            Dictionary containing heart rate data for the specified date.

        Raises:
            ValueError: If cdate format is invalid.
            GarminConnectConnectionError: If no data received.
            GarminConnectAuthenticationError: If authentication fails.

        """
        cdate = validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_heartrates_daily_url}/{self.display_name}"
        params = {"date": cdate}
        logger.debug("Requesting heart rates")

        response = self.connectapi(url, params=params)

        if response is None:
            raise GarminConnectConnectionError("No heart rate data received")

        return response
