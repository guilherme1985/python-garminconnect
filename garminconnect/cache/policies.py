"""TTL policies per endpoint (F5-02).

Endpoints map by URL prefix to TTL in seconds. Long TTLs are for
historical / immutable data; short TTLs for "today" intra-day series
that the watch still updates.
"""

from __future__ import annotations

# Order matters: first prefix match wins. Keep specific prefixes first.
TTL_POLICIES: list[tuple[str, float]] = [
    # 24h — past activities, immutable
    ("/activity-service/activity",                     86400),
    ("/activitylist-service/activities/search",         3600),
    # 5min — daily aggregates that still update during the current day
    ("/usersummary-service/usersummary",                 300),
    ("/wellness-service/wellness/dailyHeartRate",        300),
    ("/wellness-service/wellness/dailyStress",           300),
    ("/sleep-service/sleep",                             300),
    ("/wellness-service/wellness/dailySpo2",             300),
    ("/wellness-service/wellness/dailyRespiration",      300),
    # 5min — body battery (refreshes very often)
    ("/wellness-service/wellness/bodyBattery",           300),
    # 24h — long historical ranges (weeks, weight, badges)
    ("/biometric-service/biometric",                   86400),
    ("/weight-service/weight",                         86400),
    ("/badge-service/badge",                           86400),
    ("/goal-service/goal",                              3600),
    # 7d — profile, devices, settings
    ("/userprofile-service/userprofile",              604800),
    ("/device-service/deviceregistration",            604800),
    # 5min — default fallback
    ("",                                                 300),
]


def ttl_for(path: str) -> float:
    """Return the configured TTL (seconds) for an endpoint path."""
    for prefix, ttl in TTL_POLICIES:
        if path.startswith(prefix):
            return ttl
    return 300
