"""Hydration, nutrition, menstrual cycle and pregnancy domain methods."""

from __future__ import annotations

import logging
import numbers
from datetime import date, datetime
from typing import Any

from .._internal import fmt_ts
from ..validation.validators import (
    DATE_FORMAT_STR,
    MAX_HYDRATION_ML,
    validate_date_format,
)

logger = logging.getLogger(__name__)


class NutritionMixin:
    """Mixin providing hydration, nutrition, menstrual and pregnancy methods."""

    connectapi: Any
    client: Any
    garmin_connect_set_hydration_url: str
    garmin_connect_daily_hydration_url: str
    garmin_connect_menstrual_dayview_url: str
    garmin_connect_menstrual_calendar_url: str
    garmin_connect_pregnancy_snapshot_url: str
    garmin_connect_nutrition_daily_food_logs: str
    garmin_connect_nutrition_daily_meals: str
    garmin_connect_nutrition_daily_settings: str

    # ------------------------------------------------------------------ #
    #  Hydration                                                         #
    # ------------------------------------------------------------------ #

    def add_hydration_data(
        self,
        value_in_ml: float,
        timestamp: str | None = None,
        cdate: str | None = None,
    ) -> dict[str, Any]:
        """Add hydration data in ml.  Defaults to current date and current timestamp if left empty.

        :param float required - value_in_ml: The number of ml of water you wish to add (positive) or subtract (negative)
        :param timestamp optional - timestamp: The timestamp of the hydration update, format 'YYYY-MM-DDThh:mm:ss.ms' Defaults to current timestamp
        :param date optional - cdate: The date of the weigh in, format 'YYYY-MM-DD'. Defaults to current date.
        """
        if not isinstance(value_in_ml, numbers.Real):
            raise ValueError("value_in_ml must be a number")

        if abs(value_in_ml) > MAX_HYDRATION_ML:
            raise ValueError(
                f"value_in_ml seems unreasonably high (>{MAX_HYDRATION_ML}ml)"
            )

        url = self.garmin_connect_set_hydration_url

        if timestamp is None and cdate is None:
            raw_date = date.today()
            cdate = str(raw_date)

            raw_ts = datetime.now()
            timestamp = fmt_ts(raw_ts)

        elif cdate is not None and timestamp is None:
            cdate = validate_date_format(cdate, "cdate")
            raw_ts = datetime.strptime(cdate, DATE_FORMAT_STR)  # midnight local
            timestamp = fmt_ts(raw_ts)

        elif cdate is None and timestamp is not None:
            if not isinstance(timestamp, str):
                raise ValueError("timestamp must be a string")
            try:
                try:
                    raw_ts = datetime.fromisoformat(timestamp)
                except ValueError:
                    raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                cdate = raw_ts.date().isoformat()
                timestamp = fmt_ts(raw_ts)
            except ValueError as e:
                raise ValueError("invalid timestamp format (expected ISO 8601)") from e
        else:
            cdate = validate_date_format(cdate, "cdate")
            if not isinstance(timestamp, str):
                raise ValueError("timestamp must be a string")
            try:
                try:
                    raw_ts = datetime.fromisoformat(timestamp)
                except ValueError:
                    raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                ts_date = raw_ts.date().isoformat()
                if ts_date != cdate:
                    raise ValueError(
                        f"timestamp date ({ts_date}) doesn't match cdate ({cdate})"
                    )
                timestamp = fmt_ts(raw_ts)
            except ValueError:
                raise

        payload = {
            "calendarDate": cdate,
            "timestampLocal": timestamp,
            "valueInML": value_in_ml,
        }

        logger.debug("Adding hydration data")
        return self.client.put("connectapi", url, json=payload).json()

    def get_hydration_data(self, cdate: str) -> dict[str, Any]:
        """Return available hydration data 'cdate' format 'YYYY-MM-DD'."""
        cdate = validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_hydration_url}/{cdate}"
        logger.debug("Requesting hydration data")

        return self.connectapi(url)

    # ------------------------------------------------------------------ #
    #  Menstrual cycle                                                   #
    # ------------------------------------------------------------------ #

    def get_menstrual_data_for_date(self, fordate: str) -> dict[str, Any]:
        """Return menstrual data for date.

        Requires Cycle Tracking enabled in the Garmin profile. Returns an
        empty dict for accounts without tracking active.
        """
        fordate = validate_date_format(fordate, "fordate")
        url = f"{self.garmin_connect_menstrual_dayview_url}/{fordate}"
        logger.debug("Requesting menstrual data for date %s", fordate)

        return self.connectapi(url)

    def get_menstrual_calendar_data(
        self, startdate: str, enddate: str
    ) -> dict[str, Any]:
        """Return summaries of cycles that have days between startdate and enddate."""
        startdate = validate_date_format(startdate, "startdate")
        enddate = validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_menstrual_calendar_url}/{startdate}/{enddate}"
        logger.debug(
            "Requesting menstrual data for dates %s through %s", startdate, enddate
        )

        return self.connectapi(url)

    # ------------------------------------------------------------------ #
    #  Pregnancy                                                         #
    # ------------------------------------------------------------------ #

    def get_pregnancy_summary(self) -> dict[str, Any]:
        """Return snapshot of pregnancy data.

        Requires Pregnancy Tracking enabled in the Garmin profile. Returns
        an empty dict for accounts without active pregnancy tracking.
        """
        url = f"{self.garmin_connect_pregnancy_snapshot_url}"
        logger.debug("Requesting pregnancy snapshot data")

        return self.connectapi(url)

    # ------------------------------------------------------------------ #
    #  Nutrition                                                         #
    # ------------------------------------------------------------------ #

    def get_nutrition_daily_food_log(self, cdate: str) -> dict[str, Any]:
        """Return food log summary for 'cdate' format 'YYYY-MM-DD'."""
        cdate = validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_nutrition_daily_food_logs}/{cdate}"
        logger.debug("Requesting nutrition food log data for date %s", cdate)
        return self.connectapi(url)

    def get_nutrition_daily_meals(self, cdate: str) -> dict[str, Any]:
        """Return meals summary for 'cdate' format 'YYYY-MM-DD'."""
        cdate = validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_nutrition_daily_meals}/{cdate}"
        logger.debug("Requesting nutrition meals data for date %s", cdate)
        return self.connectapi(url)

    def get_nutrition_daily_settings(self, cdate: str) -> dict[str, Any]:
        """Return nutrition settings for 'cdate' format 'YYYY-MM-DD'.

        Returns an empty dict when nutrition tracking has never been
        configured for this account.
        """
        cdate = validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_nutrition_daily_settings}/{cdate}"
        logger.debug("Requesting nutrition settings data for date %s", cdate)
        return self.connectapi(url)
