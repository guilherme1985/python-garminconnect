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
    # 1h — slowly changing daily aggregates
    ("/usersummary-service/usersummary",                3600),
    ("/wellness-service/wellness/dailyHeartRate",       3600),
    ("/wellness-service/wellness/dailyStress",          3600),
    ("/sleep-service/sleep",                            3600),
    ("/wellness-service/wellness/dailySpo2",            3600),
    ("/wellness-service/wellness/dailyRespiration",     3600),
    # 15min — body battery (refreshes more often)
    ("/wellness-service/wellness/bodyBattery",           900),
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
