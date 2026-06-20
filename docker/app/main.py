"""FastAPI dashboard for python-garminconnect."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from garmin_service import days_ago, get_client, safe_call, yesterday
from scheduler import STATE, force_sync, run_collector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dashboard")

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background collector if InfluxDB is reachable."""
    task: asyncio.Task | None = None
    if os.getenv("INFLUX_URL"):
        interval = float(os.getenv("COLLECT_INTERVAL_S", "900"))
        task = asyncio.create_task(run_collector(interval))
        logger.info("collector started (interval=%.0fs)", interval)
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="Garmin Connect Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


PAGES = [
    ("dashboard", "Resumo",         "/",              "📊"),
    ("steps",     "Passos",         "/steps",         "👟"),
    ("heart",     "Coração",        "/heart",         "❤️"),
    ("sleep",     "Sono",           "/sleep",         "😴"),
    ("stress",    "Estresse",       "/stress",        "🧘"),
    ("battery",   "Body Battery",   "/battery",       "🔋"),
    ("activities","Atividades",     "/activities",    "🏃"),
    ("weight",    "Peso",           "/weight",        "⚖️"),
    ("hrv",       "HRV",            "/hrv",           "📈"),
    ("training",  "Treino",         "/training",      "🏋️"),
]


def _ctx(request: Request, **extra: Any) -> dict[str, Any]:
    return {"request": request, "pages": PAGES, "active": "", **extra}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sync/status")
async def api_sync_status() -> JSONResponse:
    """Return current collector state (for sidebar polling)."""
    return JSONResponse({
        "running":     STATE.lock.locked(),
        "last_run_at": STATE.last_run_at.isoformat() if STATE.last_run_at else None,
        "next_run_at": STATE.next_run_at.isoformat() if STATE.next_run_at else None,
        "last_status": STATE.last_status,
        "last_points": STATE.last_points,
        "last_error":  STATE.last_error,
        "interval_s":  STATE.interval_s,
        "runs_total":  STATE.runs_total,
        "runs_ok":     STATE.runs_ok,
        "enabled":     bool(os.getenv("INFLUX_URL")),
    })


@app.post("/api/sync")
async def api_sync() -> JSONResponse:
    """Run a collector iteration on demand."""
    if not os.getenv("INFLUX_URL"):
        return JSONResponse(
            {"status": "disabled",
             "error": "INFLUX_URL não configurado — coletor inativo"},
            status_code=400,
        )
    if STATE.lock.locked():
        return JSONResponse(
            {"status": "busy", "msg": "sync já em andamento"},
            status_code=409,
        )
    await force_sync()
    return JSONResponse({
        "status":      STATE.last_status,
        "last_run_at": STATE.last_run_at.isoformat() if STATE.last_run_at else None,
        "last_points": STATE.last_points,
        "last_error":  STATE.last_error,
    })


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    """Resumo do dia anterior + métricas-chave."""
    d = yesterday()
    cards = []
    summary, err = safe_call("get_user_summary", d)
    if summary:
        # OMS / Garmin: vigorous intensity counts double.
        mod = summary.get("moderateIntensityMinutes") or 0
        vig = summary.get("vigorousIntensityMinutes") or 0
        goal = summary.get("intensityMinutesGoal") or 0
        intensity_total = mod + 2 * vig
        intensity_label = f"{intensity_total} / {goal}" if goal else intensity_total
        cards = [
            ("Passos",      summary.get("totalSteps", 0),                    "👟"),
            ("Calorias",    round(summary.get("totalKilocalories") or 0),    "🔥"),
            ("Distância",   f"{(summary.get('totalDistanceMeters') or 0)/1000:.2f} km", "📏"),
            ("FC repouso",  summary.get("restingHeartRate", "—"),            "❤️"),
            ("Andares",     summary.get("floorsAscended", 0),                "🏢"),
            ("Min. intens.",intensity_label,                                 "⚡"),
            ("Stress méd.", summary.get("averageStressLevel", "—"),          "🧘"),
            ("Body Battery",summary.get("bodyBatteryHighestValue", "—"),     "🔋"),
        ]

    user, _ = safe_call("get_full_name")
    return templates.TemplateResponse(
        "dashboard.html",
        _ctx(request, active="dashboard", cards=cards, error=err,
             user=user or "", report_date=d),
    )


# ---------- páginas (HTML que consome /api/...) -------------------- #


def _page(name: str, title: str):
    def _view(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "chart_page.html",
            _ctx(request, active=name, title=title, endpoint=f"/api/{name}"),
        )
    return _view


app.get("/steps",      response_class=HTMLResponse)(_page("steps",      "Passos (últimos 30 dias)"))
app.get("/heart",      response_class=HTMLResponse)(_page("heart",      "Frequência cardíaca (ontem)"))
app.get("/sleep",      response_class=HTMLResponse)(_page("sleep",      "Sono (últimos 14 dias)"))
app.get("/stress",     response_class=HTMLResponse)(_page("stress",     "Estresse (últimos 7 dias)"))
app.get("/battery",    response_class=HTMLResponse)(_page("battery",    "Body Battery (últimos 7 dias)"))
app.get("/weight",     response_class=HTMLResponse)(_page("weight",     "Peso (últimos 90 dias)"))
app.get("/hrv",        response_class=HTMLResponse)(_page("hrv",        "HRV (ontem)"))
app.get("/training",   response_class=HTMLResponse)(_page("training",   "Training readiness (ontem)"))


@app.get("/activities", response_class=HTMLResponse)
def activities(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "activities.html", _ctx(request, active="activities"),
    )


# ---------- API JSON --------------------------------------------------- #


@app.get("/api/steps")
def api_steps() -> JSONResponse:
    data, err = safe_call("get_daily_steps", days_ago(30), yesterday())
    if err:
        return JSONResponse({"error": err}, status_code=502)
    labels = [d.get("calendarDate") for d in data or []]
    values = [d.get("totalSteps") or 0 for d in data or []]
    goals  = [d.get("stepGoal") or 0 for d in data or []]
    return JSONResponse({
        "chart": {
            "type": "bar",
            "labels": labels,
            "datasets": [
                {"label": "Passos", "data": values, "backgroundColor": "#3b82f6"},
                {"label": "Meta",   "data": goals,  "type": "line", "borderColor": "#f59e0b", "backgroundColor": "transparent"},
            ],
        },
        "table": [{"data": d.get("calendarDate"),
                   "passos": d.get("totalSteps"),
                   "meta": d.get("stepGoal"),
                   "distância (m)": d.get("totalDistance")} for d in data or []],
    })


@app.get("/api/heart")
def api_heart() -> JSONResponse:
    d = yesterday()
    data, err = safe_call("get_heart_rates", d)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    samples = (data or {}).get("heartRateValues") or []
    labels = [_ms_to_hhmm(s[0]) for s in samples]
    values = [s[1] for s in samples]
    return JSONResponse({
        "chart": {
            "type": "line",
            "labels": labels,
            "datasets": [{
                "label": "FC (bpm)", "data": values,
                "borderColor": "#ef4444", "backgroundColor": "rgba(239,68,68,0.15)",
                "tension": 0.2, "pointRadius": 0,
            }],
        },
        "table": [
            {"métrica": "Resting HR",  "valor": data.get("restingHeartRate")},
            {"métrica": "Min HR",      "valor": data.get("minHeartRate")},
            {"métrica": "Max HR",      "valor": data.get("maxHeartRate")},
            {"métrica": "Last 7d avg", "valor": data.get("lastSevenDaysAvgRestingHeartRate")},
        ] if isinstance(data, dict) else [],
    })


@app.get("/api/sleep")
def api_sleep() -> JSONResponse:
    labels, deep, light, rem, awake = [], [], [], [], []
    for n in range(14, 0, -1):
        d = (date.today() - timedelta(days=n)).isoformat()
        v, _ = safe_call("get_sleep_data", d)
        labels.append(d)
        dto = (v or {}).get("dailySleepDTO") or {}
        deep.append(round((dto.get("deepSleepSeconds") or 0) / 3600, 2))
        light.append(round((dto.get("lightSleepSeconds") or 0) / 3600, 2))
        rem.append(round((dto.get("remSleepSeconds") or 0) / 3600, 2))
        awake.append(round((dto.get("awakeSleepSeconds") or 0) / 3600, 2))
    return JSONResponse({
        "chart": {
            "type": "bar",
            "labels": labels,
            "datasets": [
                {"label": "Profundo", "data": deep,  "backgroundColor": "#1e40af", "stack": "s"},
                {"label": "Leve",     "data": light, "backgroundColor": "#3b82f6", "stack": "s"},
                {"label": "REM",      "data": rem,   "backgroundColor": "#8b5cf6", "stack": "s"},
                {"label": "Acordado", "data": awake, "backgroundColor": "#ef4444", "stack": "s"},
            ],
        },
        "table": [{"data": d, "profundo (h)": p, "leve (h)": l, "REM (h)": r, "acordado (h)": a}
                  for d, p, l, r, a in zip(labels, deep, light, rem, awake)],
    })


@app.get("/api/stress")
def api_stress() -> JSONResponse:
    labels, avg, mx = [], [], []
    for n in range(7, 0, -1):
        d = (date.today() - timedelta(days=n)).isoformat()
        v, _ = safe_call("get_stress_data", d)
        labels.append(d)
        avg.append((v or {}).get("avgStressLevel") or 0)
        mx.append((v or {}).get("maxStressLevel") or 0)
    return JSONResponse({
        "chart": {
            "type": "bar", "labels": labels,
            "datasets": [
                {"label": "Médio", "data": avg, "backgroundColor": "#22c55e"},
                {"label": "Máx",   "data": mx,  "backgroundColor": "#ef4444"},
            ],
        },
        "table": [{"data": d, "médio": a, "máx": m} for d, a, m in zip(labels, avg, mx)],
    })


@app.get("/api/battery")
def api_battery() -> JSONResponse:
    data, err = safe_call("get_body_battery", days_ago(7), yesterday())
    if err:
        return JSONResponse({"error": err}, status_code=502)
    labels = [d.get("date") for d in data or []]
    charged = [d.get("charged") for d in data or []]
    drained = [d.get("drained") for d in data or []]
    return JSONResponse({
        "chart": {
            "type": "bar", "labels": labels,
            "datasets": [
                {"label": "Carregado", "data": charged, "backgroundColor": "#22c55e"},
                {"label": "Drenado",   "data": drained, "backgroundColor": "#ef4444"},
            ],
        },
        "table": [{"data": d.get("date"),
                   "carregado": d.get("charged"),
                   "drenado":   d.get("drained")} for d in data or []],
    })


@app.get("/api/weight")
def api_weight() -> JSONResponse:
    data, err = safe_call("get_weigh_ins", days_ago(90), yesterday())
    if err:
        return JSONResponse({"error": err}, status_code=502)
    entries = []
    if isinstance(data, dict):
        for daily in data.get("dailyWeightSummaries", []) or []:
            for wi in daily.get("allWeightMetrics", []) or []:
                entries.append({
                    "data": daily.get("summaryDate"),
                    "peso (kg)": round((wi.get("weight") or 0)/1000, 2),
                    "imc": wi.get("bmi"),
                    "gordura (%)": wi.get("bodyFat"),
                })
    entries.sort(key=lambda e: e["data"] or "")
    return JSONResponse({
        "chart": {
            "type": "line",
            "labels": [e["data"] for e in entries],
            "datasets": [{
                "label": "Peso (kg)", "data": [e["peso (kg)"] for e in entries],
                "borderColor": "#3b82f6", "backgroundColor": "rgba(59,130,246,0.15)",
                "tension": 0.25,
            }],
        },
        "table": entries,
    })


@app.get("/api/hrv")
def api_hrv() -> JSONResponse:
    d = yesterday()
    data, err = safe_call("get_hrv_data", d)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    readings = ((data or {}).get("hrvReadings")) or []
    labels = [_ms_to_hhmm(r.get("readingTimeGMT")) if isinstance(r.get("readingTimeGMT"), int)
              else r.get("readingTimeLocal") for r in readings]
    values = [r.get("hrvValue") for r in readings]
    summary = (data or {}).get("hrvSummary") or {}
    return JSONResponse({
        "chart": {
            "type": "line", "labels": labels,
            "datasets": [{
                "label": "HRV (ms)", "data": values,
                "borderColor": "#8b5cf6", "backgroundColor": "rgba(139,92,246,0.15)",
                "tension": 0.2,
            }],
        },
        "table": [
            {"métrica": "Status",      "valor": summary.get("status")},
            {"métrica": "Último valor","valor": summary.get("lastNightAvg")},
            {"métrica": "5min máx",    "valor": summary.get("lastNight5MinHigh")},
            {"métrica": "Min linha base","valor": summary.get("baseline", {}).get("lowUpper") if isinstance(summary.get("baseline"), dict) else None},
        ],
    })


@app.get("/api/training")
def api_training() -> JSONResponse:
    d = yesterday()
    data, err = safe_call("get_training_readiness", d)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    entries = data or []
    if not entries:
        return JSONResponse({"chart": None, "table": []})
    e = entries[0] if isinstance(entries, list) else entries
    return JSONResponse({
        "chart": None,
        "table": [
            {"métrica": "Nível",        "valor": e.get("level")},
            {"métrica": "Score",        "valor": e.get("score")},
            {"métrica": "Sono",         "valor": e.get("sleepScore")},
            {"métrica": "Recuperação",  "valor": e.get("recoveryTime")},
            {"métrica": "HRV (status)", "valor": e.get("hrvStatus")},
            {"métrica": "Stress",       "valor": e.get("acuteLoad")},
        ],
    })


@app.get("/api/activities")
def api_activities() -> JSONResponse:
    data, err = safe_call("get_activities", 0, 50)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    rows = []
    for a in (data or [])[:50]:
        rows.append({
            "data": (a.get("startTimeLocal") or "")[:19].replace("T", " "),
            "tipo": (a.get("activityType") or {}).get("typeKey"),
            "nome": a.get("activityName"),
            "distância (km)": round((a.get("distance") or 0)/1000, 2),
            "duração (min)": round((a.get("duration") or 0)/60, 1),
            "calorias": round(a.get("calories") or 0),
            "fc média": a.get("averageHR"),
            "fc máx": a.get("maxHR"),
        })
    types_counter: dict[str, int] = {}
    for r in rows:
        t = r["tipo"] or "—"
        types_counter[t] = types_counter.get(t, 0) + 1
    return JSONResponse({
        "chart": {
            "type": "doughnut",
            "labels": list(types_counter.keys()),
            "datasets": [{
                "data": list(types_counter.values()),
                "backgroundColor": ["#3b82f6","#22c55e","#ef4444","#f59e0b","#8b5cf6","#ec4899","#06b6d4","#84cc16"],
            }],
        },
        "table": rows,
    })


# ---------- helpers ---------------------------------------------------- #


def _ms_to_hhmm(value: Any) -> str:
    """Convert epoch-ms to HH:MM (UTC)."""
    if not isinstance(value, int):
        return str(value)
    import time
    return time.strftime("%H:%M", time.gmtime(value / 1000))


@app.exception_handler(Exception)
async def default_handler(request: Request, exc: Exception) -> HTMLResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return templates.TemplateResponse(
        "error.html",
        _ctx(request, error=f"{type(exc).__name__}: {exc}"),
        status_code=500,
    )
