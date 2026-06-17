"""Goals, badges, challenges and personal records domain methods."""

from __future__ import annotations

import logging
from typing import Any

from ..validation.validators import (
    validate_non_negative_integer,
    validate_positive_integer,
)

logger = logging.getLogger(__name__)


class GoalsMixin:
    """Mixin providing personal records, badges, challenges and goals methods."""

    connectapi: Any
    display_name: str | None
    garmin_connect_personal_record_url: str
    garmin_connect_earned_badges_url: str
    garmin_connect_available_badges_url: str
    garmin_connect_adhoc_challenges_url: str
    garmin_connect_badge_challenges_url: str
    garmin_connect_available_badge_challenges_url: str
    garmin_connect_non_completed_badge_challenges_url: str
    garmin_connect_inprogress_virtual_challenges_url: str
    garmin_connect_goals_url: str

    # ------------------------------------------------------------------ #
    #  Personal records                                                  #
    # ------------------------------------------------------------------ #

    def get_personal_record(self) -> dict[str, Any]:
        """Return personal records for current user."""
        url = f"{self.garmin_connect_personal_record_url}/{self.display_name}"
        logger.debug("Requesting personal records for user")

        return self.connectapi(url)

    # ------------------------------------------------------------------ #
    #  Badges                                                            #
    # ------------------------------------------------------------------ #

    def get_earned_badges(self) -> list[dict[str, Any]]:
        """Return earned badges for current user."""
        url = self.garmin_connect_earned_badges_url
        logger.debug("Requesting earned badges for user")

        return self.connectapi(url)

    def get_available_badges(self) -> list[dict[str, Any]]:
        """Return available badges for current user."""
        url = self.garmin_connect_available_badges_url
        logger.debug("Requesting available badges for user")

        return self.connectapi(url, params={"showExclusiveBadge": "true"})

    def get_in_progress_badges(self) -> list[dict[str, Any]]:
        """Return in progress badges for current user."""
        logger.debug("Requesting in progress badges for user")

        earned_badges = self.get_earned_badges()
        available_badges = self.get_available_badges()

        # Filter out badges that are not in progress
        def is_badge_in_progress(badge: dict) -> bool:
            """Return True if the badge is in progress."""
            progress = badge.get("badgeProgressValue")
            if not progress:
                return False
            if progress == 0:
                return False
            target = badge.get("badgeTargetValue")
            if progress == target:
                if badge.get("badgeLimitCount") is None:
                    return False
                return badge.get("badgeEarnedNumber", 0) < badge["badgeLimitCount"]
            return True

        earned_in_progress_badges = list(filter(is_badge_in_progress, earned_badges))
        available_in_progress_badges = list(
            filter(is_badge_in_progress, available_badges)
        )

        combined = {b["badgeId"]: b for b in earned_in_progress_badges}
        combined.update({b["badgeId"]: b for b in available_in_progress_badges})
        return list(combined.values())

    # ------------------------------------------------------------------ #
    #  Challenges                                                        #
    # ------------------------------------------------------------------ #

    def get_adhoc_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return adhoc challenges for current user."""
        start = validate_non_negative_integer(start, "start")
        limit = validate_positive_integer(limit, "limit")
        url = self.garmin_connect_adhoc_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting adhoc challenges for user")

        return self.connectapi(url, params=params)

    def get_badge_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return badge challenges for current user."""
        start = validate_non_negative_integer(start, "start")
        limit = validate_positive_integer(limit, "limit")
        url = self.garmin_connect_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_available_badge_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return available badge challenges."""
        start = validate_non_negative_integer(start, "start")
        limit = validate_positive_integer(limit, "limit")
        url = self.garmin_connect_available_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting available badge challenges")

        return self.connectapi(url, params=params)

    def get_non_completed_badge_challenges(
        self, start: int, limit: int
    ) -> dict[str, Any]:
        """Return badge non-completed challenges for current user."""
        start = validate_non_negative_integer(start, "start")
        limit = validate_positive_integer(limit, "limit")
        url = self.garmin_connect_non_completed_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_inprogress_virtual_challenges(
        self, start: int, limit: int
    ) -> dict[str, Any]:
        """Return in-progress virtual challenges for current user."""
        start = validate_positive_integer(start, "start")
        limit = validate_positive_integer(limit, "limit")
        url = self.garmin_connect_inprogress_virtual_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting in-progress virtual challenges for user")

        return self.connectapi(url, params=params)

    # ------------------------------------------------------------------ #
    #  Goals                                                             #
    # ------------------------------------------------------------------ #

    def get_goals(
        self, status: str = "active", start: int = 0, limit: int = 30
    ) -> list[dict[str, Any]]:
        """Fetch all goals based on status.

        :param status: Status of goals (valid options are "active", "future", or "past")
        :type status: str
        :param start: Initial goal index
        :type start: int
        :param limit: Pagination limit when retrieving goals
        :type limit: int
        :return: list of goals in JSON format.
        """
        goals = []
        url = self.garmin_connect_goals_url
        valid_statuses = {"active", "future", "past"}
        if status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        start = validate_non_negative_integer(start, "start")
        limit = validate_positive_integer(limit, "limit")
        params = {
            "status": status,
            "start": str(start),
            "limit": str(limit),
            "sortOrder": "asc",
        }

        logger.debug("Requesting %s goals", status)
        while True:
            params["start"] = str(start)
            logger.debug(
                "Requesting %s goals %d to %d", status, start, start + limit - 1
            )
            goals_json = self.connectapi(url, params=params)
            if goals_json:
                goals.extend(goals_json)
                start = start + limit
            else:
                break

        return goals
