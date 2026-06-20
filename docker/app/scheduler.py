"""Background collector — periodically pushes Garmin metrics to InfluxDB.

Runs inside the dashboard process via FastAPI lifespan. No Celery, no
APScheduler — just an asyncio task with sleep.

Series written:
    measurement=health, fields=steps,calories,resting_hr,intensity_min,
                                 floors,body_battery,stress_avg
    measurement=sleep,  fields=deep_h,light_h,rem_h,awake_h,total_h
    measurement=weight, fields=weight_kg,bmi,body_fat
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

from garmin_service import get_client

logger = logging.getLogger("scheduler")


# ----------------- shared state (observable from /api/sync) ---------- #


@dataclass
class CollectorState:
    """Single source of truth for the dashboard sync indicator."""
    last_run_at: datetime | None = None
    last_status: str = "idle"          # idle | running | ok | error
    last_points: int = 0
    last_error: str | None = None
    next_run_at: datetime | None = None
    interval_s: float = 900.0
    runs_total: int = 0
    runs_ok: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


STATE = CollectorState()


def _influx_url() -> str:
    return os.getenv("INFLUX_URL", "http://influxdb:8086")


def _influx_write(points: list[str]) -> None:
    if not points:
        return
    url = (
        f"{_influx_url()}/api/v2/write"
        f"?org={os.getenv('INFLUX_ORG', 'garmin')}"
        f"&bucket={os.getenv('INFLUX_BUCKET', 'metrics')}"
        f"&precision=s"
    )
    body = "\n".join(points).encode()
    req = urlrequest.Request(
        url, data=body, method="POST",
        headers={
            "Authorization": f"Token {os.getenv('INFLUX_TOKEN', '')}",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
    try:
        with urlrequest.urlopen(req, timeout=10) as resp:
            if resp.status >= 300:
                logger.warning("influx write status=%s", resp.status)
    except urlerror.URLError as exc:
        logger.warning("influx write failed: %s", exc)


def _line(measurement: str, tags: dict[str, str], fields: dict[str, Any],
          ts_s: int) -> str | None:
    """Encode one line-protocol line, skipping null fields."""
    payload = {k: v for k, v in fields.items() if v is not None}
    if not payload:
        return None
    tag_str = ",".join(f"{k}={v}" for k, v in tags.items() if v)
    field_str = ",".join(
        f"{k}={v}" if isinstance(v, (int, float)) and not isinstance(v, bool)
        else f'{k}="{v}"'
        for k, v in payload.items()
    )
    head = f"{measurement},{tag_str}" if tag_str else measurement
    return f"{head} {field_str} {ts_s}"


def _collect(days: int = 7) -> list[str]:
    """Pull last N days INCLUDING TODAY; build InfluxDB line protocol."""
    g = get_client()
    # Drop any cached "empty today" so we always re-pull today's partial day.
    try:
        g.clear_cache()
    except Exception:  # noqa: BLE001
        pass
    points: list[str] = []
    today = date.today()
    # range(days, -1, -1) = [days, days-1, ..., 1, 0]  → inclui n=0 (hoje)
    for n in range(days, -1, -1):
        d = (today - timedelta(days=n)).isoformat()
        ts = int(time.mktime(time.strptime(d, "%Y-%m-%d")))

        try:
            summary = g.get_user_summary(d) or {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("summary %s: %s", d, exc)
            summary = {}
        ln = _line("health", {"date": d}, {
            "steps":          summary.get("totalSteps"),
            "calories":       summary.get("totalKilocalories"),
            "resting_hr":     summary.get("restingHeartRate"),
            "intensity_min":  ((summary.get("moderateIntensityMinutes") or 0)
                              + 2 * (summary.get("vigorousIntensityMinutes") or 0)) or None,
            "floors":         summary.get("floorsAscended"),
            "body_battery":   summary.get("bodyBatteryHighestValue"),
            "stress_avg":     summary.get("averageStressLevel"),
        }, ts)
        if ln: points.append(ln)

        try:
            sleep = g.get_sleep_data(d) or {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("sleep %s: %s", d, exc)
            sleep = {}
        dto = (sleep.get("dailySleepDTO") or {})
        ln = _line("sleep", {"date": d}, {
            "deep_h":  round((dto.get("deepSleepSeconds") or 0) / 3600, 2) or None,
            "light_h": round((dto.get("lightSleepSeconds") or 0) / 3600, 2) or None,
            "rem_h":   round((dto.get("remSleepSeconds") or 0) / 3600, 2) or None,
            "awake_h": round((dto.get("awakeSleepSeconds") or 0) / 3600, 2) or None,
            "total_h": round((dto.get("sleepTimeSeconds") or 0) / 3600, 2) or None,
        }, ts)
        if ln: points.append(ln)

    # weight: single range pull (last 30 days)
    try:
        w = g.get_weigh_ins(
            (today - timedelta(days=30)).isoformat(), today.isoformat(),
        ) or {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("weight: %s", exc)
        w = {}
    if isinstance(w, dict):
        for daily in w.get("dailyWeightSummaries", []) or []:
            d = daily.get("summaryDate")
            if not d:
                continue
            ts = int(time.mktime(time.strptime(d, "%Y-%m-%d")))
            metrics = (daily.get("allWeightMetrics") or [{}])[0]
            ln = _line("weight", {"date": d}, {
                "weight_kg": round((metrics.get("weight") or 0) / 1000, 2) or None,
                "bmi":       metrics.get("bmi"),
                "body_fat":  metrics.get("bodyFat"),
            }, ts)
            if ln: points.append(ln)

    return points


async def _run_once(days: int = 7) -> None:
    """Single collect→write iteration that updates STATE."""
    if STATE.lock.locked():
        logger.warning("sync requested but one is already running — ignored")
        return
    async with STATE.lock:
        STATE.last_status = "running"
        STATE.runs_total += 1
        try:
            points = await asyncio.to_thread(_collect, days)
            await asyncio.to_thread(_influx_write, points)
            STATE.last_points = len(points)
            STATE.last_status = "ok"
            STATE.last_error = None
            STATE.runs_ok += 1
            logger.info("sync OK — %d points written to influx", len(points))
        except Exception as exc:  # noqa: BLE001
            STATE.last_status = "error"
            STATE.last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("sync FAILED: %s", exc)
        finally:
            STATE.last_run_at = datetime.now()


async def force_sync(days: int = 7) -> None:
    """Trigger a one-off sync out of band (used by /api/sync endpoint)."""
    await _run_once(days)


async def run_collector(interval_s: float = 900.0) -> None:
    """Loop: collect → write → sleep. Cancellable via lifespan shutdown."""
    STATE.interval_s = interval_s
    logger.info("collector started (interval=%.0fs)", interval_s)
    while True:
        await _run_once()
        STATE.next_run_at = datetime.now() + timedelta(seconds=interval_s)
        try:
            await asyncio.sleep(interval_s)
        except asyncio.CancelledError:
            logger.info("collector cancelled")
            raise
