"""Cache layer for python-garminconnect (F5-02).

Public surface:

    from garminconnect.cache import (
        CacheBackend, InMemoryCache, DiskCache, TTL_POLICIES, ttl_for,
    )

A cache backend can be plugged into ``Garmin`` via the ``cache`` kwarg:

    from garminconnect import Garmin
    from garminconnect.cache import DiskCache

    g = Garmin(email, password, cache=DiskCache("~/.garminconnect/cache"))
    g.login()
    # Second identical call returns the cached value (within TTL).
    g.get_stats("2026-06-19")
"""

from .backend import CacheBackend
from .disk import DiskCache
from .memory import InMemoryCache
from .policies import TTL_POLICIES, ttl_for

__all__ = [
    "CacheBackend",
    "DiskCache",
    "InMemoryCache",
    "TTL_POLICIES",
    "ttl_for",
]
