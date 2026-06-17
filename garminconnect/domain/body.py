"""Body composition, weight and blood pressure domain methods.

Provides the BodyMixin class with methods for body composition tracking,
weight management and blood pressure measurements.

This mixin assumes the host class provides:
    - self.connectapi(url, **kwargs)
    - self.client.post(...) / self.client.request(...)
    - self.garmin_connect_weight_url
    - self.garmin_connect_upload
    - self.garmin_connect_blood_pressure_endpoint
    - self.garmin_connect_set_blood_pressure_endpoint
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .._internal import VALID_WEIGHT_UNITS, fmt_ts, validate_json_exists
from ..fit import FitEncoderWeight
from ..validation.validators import (
    DATE_FORMAT_STR,
    validate_date_format,
    validate_positive_number,
)

logger = logging.getLogger(__name__)


class BodyMixin:
    """Mixin providing body composition, weight and blood pressure API methods."""

    # Attributes provided by the host class (Garmin).
    connectapi: Any
    client: Any
    garmin_connect_weight_url: str
    garmin_connect_upload: str
    garmin_connect_blood_pressure_endpoint: str
    garmin_connect_set_blood_pressure_endpoint: str

    # ------------------------------------------------------------------ #
    #  Body composition                                                  #
    # ------------------------------------------------------------------ #

    def get_body_composition(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """Return available body composition data for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'.
        """
        startdate = validate_date_format(startdate, "startdate")
        enddate = (
            startdate if enddate is None else validate_date_format(enddate, "enddate")
        )
        if (
            datetime.strptime(startdate, DATE_FORMAT_STR).date()
            > datetime.strptime(enddate, DATE_FORMAT_STR).date()
        ):
            raise ValueError("startdate cannot be after enddate")
        url = f"{self.garmin_connect_weight_url}/weight/dateRange"
        params = {"startDate": str(startdate), "endDate": str(enddate)}
        logger.debug("Requesting body composition")

        return self.connectapi(url, params=params)

    def add_body_composition(
        self,
        timestamp: str | None,
        weight: float,
        percent_fat: float | None = None,
        percent_hydration: float | None = None,
        visceral_fat_mass: float | None = None,
        bone_mass: float | None = None,
        muscle_mass: float | None = None,
        basal_met: float | None = None,
        active_met: float | None = None,
        physique_rating: float | None = None,
        metabolic_age: float | None = None,
        visceral_fat_rating: float | None = None,
        bmi: float | None = None,
    ) -> dict[str, Any]:
        """Upload a body composition measurement via FIT encoding."""
        weight = validate_positive_number(weight, "weight")
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        fitEncoder = FitEncoderWeight()
        fitEncoder.write_file_info()
        fitEncoder.write_file_creator()
        fitEncoder.write_device_info(dt)
        fitEncoder.write_weight_scale(
            dt,
            weight=weight,
            percent_fat=percent_fat,
            percent_hydration=percent_hydration,
            visceral_fat_mass=visceral_fat_mass,
            bone_mass=bone_mass,
            muscle_mass=muscle_mass,
            basal_met=basal_met,
            active_met=active_met,
            physique_rating=physique_rating,
            metabolic_age=metabolic_age,
            visceral_fat_rating=visceral_fat_rating,
            bmi=bmi,
        )
        fitEncoder.finish()

        url = self.garmin_connect_upload
        files = {
            "file": ("body_composition.fit", fitEncoder.getvalue()),
        }
        return self.client.post("connectapi", url, files=files, api=True)

    # ------------------------------------------------------------------ #
    #  Weigh-ins                                                         #
    # ------------------------------------------------------------------ #

    def add_weigh_in(
        self, weight: int | float, unitKey: str = "kg", timestamp: str = ""
    ) -> dict[str, Any] | None:
        """Add a weigh-in (default to kg)."""
        weight = validate_positive_number(weight, "weight")

        if unitKey not in VALID_WEIGHT_UNITS:
            raise ValueError(f"unitKey must be one of {VALID_WEIGHT_UNITS}")

        url = f"{self.garmin_connect_weight_url}/user-weight"

        try:
            dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        except ValueError as e:
            raise ValueError(f"invalid timestamp format: {e}") from e

        dtGMT = dt.astimezone(UTC)
        payload = {
            "dateTimestamp": fmt_ts(dt),
            "gmtTimestamp": fmt_ts(dtGMT),
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }
        logger.debug("Adding weigh-in")
        return validate_json_exists(self.client.post("connectapi", url, json=payload))

    def add_weigh_in_with_timestamps(
        self,
        weight: int | float,
        unitKey: str = "kg",
        dateTimestamp: str = "",
        gmtTimestamp: str = "",
    ) -> dict[str, Any] | None:
        """Add a weigh-in with explicit timestamps (default to kg)."""
        url = f"{self.garmin_connect_weight_url}/user-weight"

        if unitKey not in VALID_WEIGHT_UNITS:
            raise ValueError(f"unitKey must be one of {VALID_WEIGHT_UNITS}")
        dt = (
            datetime.fromisoformat(dateTimestamp).astimezone()
            if dateTimestamp
            else datetime.now().astimezone()
        )
        if gmtTimestamp:
            g = datetime.fromisoformat(gmtTimestamp)
            if g.tzinfo is None:
                g = g.replace(tzinfo=UTC)
            dtGMT = g.astimezone(UTC)
        else:
            dtGMT = dt.astimezone(UTC)

        weight = validate_positive_number(weight, "weight")
        payload = {
            "dateTimestamp": fmt_ts(dt),
            "gmtTimestamp": fmt_ts(dtGMT),
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }

        logger.debug("Adding weigh-in with explicit timestamps: %s", payload)

        return validate_json_exists(self.client.post("connectapi", url, json=payload))

    def get_weigh_ins(self, startdate: str, enddate: str) -> dict[str, Any]:
        """Get weigh-ins between startdate and enddate using format 'YYYY-MM-DD'."""
        startdate = validate_date_format(startdate, "startdate")
        enddate = validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_weight_url}/weight/range/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def get_daily_weigh_ins(self, cdate: str) -> dict[str, Any]:
        """Get weigh-ins for 'cdate' format 'YYYY-MM-DD'."""
        cdate = validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_weight_url}/weight/dayview/{cdate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def delete_weigh_in(self, weight_pk: str, cdate: str) -> Any:
        """Delete specific weigh-in."""
        cdate = validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_weight_url}/weight/{cdate}/byversion/{weight_pk}"
        logger.debug("Deleting weigh-in")

        return self.client.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def delete_weigh_ins(self, cdate: str, delete_all: bool = False) -> int | None:
        """Delete weigh-in for 'cdate' format 'YYYY-MM-DD'.
        Includes option to delete all weigh-ins for that date.
        """
        daily_weigh_ins = self.get_daily_weigh_ins(cdate)
        weigh_ins = daily_weigh_ins.get("dateWeightList", [])
        if not weigh_ins or len(weigh_ins) == 0:
            logger.warning(f"No weigh-ins found on {cdate}")
            return None
        if len(weigh_ins) > 1:
            logger.warning(f"Multiple weigh-ins found for {cdate}")
            if not delete_all:
                logger.warning(
                    f"Set delete_all to True to delete all {len(weigh_ins)} weigh-ins"
                )
                return None

        for w in weigh_ins:
            self.delete_weigh_in(w["samplePk"], cdate)

        return len(weigh_ins)

    # ------------------------------------------------------------------ #
    #  Blood pressure                                                    #
    # ------------------------------------------------------------------ #

    def set_blood_pressure(
        self,
        systolic: int,
        diastolic: int,
        pulse: int,
        timestamp: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        """Add blood pressure measurement."""
        url = f"{self.garmin_connect_set_blood_pressure_endpoint}"
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        dtGMT = dt.astimezone(UTC)
        payload = {
            "measurementTimestampLocal": fmt_ts(dt),
            "measurementTimestampGMT": fmt_ts(dtGMT),
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "sourceType": "MANUAL",
            "notes": notes,
        }
        for name, val, lo, hi in (
            ("systolic", systolic, 70, 260),
            ("diastolic", diastolic, 40, 150),
            ("pulse", pulse, 20, 250),
        ):
            if not isinstance(val, int) or not (lo <= val <= hi):
                raise ValueError(f"{name} must be an int in [{lo}, {hi}]")
        logger.debug("Adding blood pressure")

        return self.client.post("connectapi", url, json=payload).json()

    def get_blood_pressure(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """Returns blood pressure by day for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'.
        """
        startdate = validate_date_format(startdate, "startdate")
        if enddate is None:
            enddate = startdate
        else:
            enddate = validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_blood_pressure_endpoint}/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting blood pressure data")

        return self.connectapi(url, params=params)

    def delete_blood_pressure(self, version: str, cdate: str) -> dict[str, Any]:
        """Delete specific blood pressure measurement."""
        url = f"{self.garmin_connect_set_blood_pressure_endpoint}/{cdate}/{version}"
        logger.debug("Deleting blood pressure measurement")

        return self.client.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        ).json()
