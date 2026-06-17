# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

Uses [PDM](https://pdm.fming.dev/) for dependency management. Requires Python 3.12+.

```bash
python3 -m venv .venv --copies
source .venv/bin/activate
pip install pdm
python -m pdm install --group :all
pre-commit install --install-hooks
```

## Common commands

```bash
pdm run format      # isort + black + ruff --fix
pdm run lint        # isort + ruff + black --check + mypy
pdm run test        # run full test suite with coverage
pdm run testcov     # test + HTML/XML coverage report
pdm run codespell   # spell check
pdm run all         # lint + codespell + pre-commit + test
```

Run a single test file:

```bash
pdm run coverage run -m pytest tests/test_garmin_unit.py -v
```

Run a specific test by name:

```bash
pdm run coverage run -m pytest tests/test_garmin_unit.py -v -k "test_name"
```

Regenerate VCR cassettes (requires real credentials via `GARMINTOKENS=~/.garminconnect`):

```bash
pdm run record-vcr
```

## Architecture

The library is a single-package (`garminconnect/`) with these main modules:

- **`__init__.py`** — `Garmin` class with all 130+ API methods. Authentication retry logic with `@functools.wraps`-decorated `connectapi()`. Exposes `g.typed` (a `TypedGarmin` proxy) when pydantic is installed.
- **`client.py`** — Authentication engine. Implements a 5-strategy chain tried in order: iOS mobile + curl_cffi → iOS mobile + requests → SSO widget + cffi → Portal + curl_cffi → Portal + requests. Each strategy handles its own login flow, token persistence, and MFA (TOTP and email-widget-based).
- **`workout.py`** — Pydantic models for typed workout construction (`SportType`, `StepType`, `ConditionType`, `TargetType`, `IntensityType`, and step/workout builder classes). Optional dependency (`garminconnect[workout]`).
- **`typed.py`** — `TypedGarmin` proxy that wraps select `Garmin` methods and validates responses into Pydantic models. Optional dependency (`garminconnect[typed]`). Experimental — shapes may change between minor releases.
- **`fit.py`** — Minimal FIT binary encoder for weight uploads (`FitEncoderWeight`).
- **`exceptions.py`** — Custom exceptions: `GarminConnectConnectionError`, `GarminConnectAuthenticationError`, `GarminConnectTooManyRequestsError`.

## Testing

Tests use [pytest-vcr](https://pytest-vcr.readthedocs.io/) with pre-recorded HTTP cassettes stored under `tests/cassettes/`. The `conftest.py` sanitizes credentials, tokens, PII, and variable headers before recording. Tests decorated with `@pytest.mark.vcr` replay cassettes without hitting the real API.

Unit tests (`test_garmin_unit.py`, `test_workout_constants.py`, `test_typed.py`, etc.) use `monkeypatch` or `pytest.fixture` fakes — no cassettes needed.

`mypy` is configured in `pyproject.toml` to skip return-type checks in test files (per convention established in PR #351); production code under `garminconnect/` is fully typed.

## Optional dependencies

| Extra | What it unlocks |
|-------|----------------|
| `garminconnect[workout]` | `workout.py` Pydantic models for typed workout uploads |
| `garminconnect[typed]` | `g.typed.*` Pydantic-validated response objects |
| `garminconnect[example]` | `readchar` for the interactive `demo.py` / `example.py` |

## Token storage

Tokens are persisted as JSON files in the directory pointed to by `GARMINTOKENS` env var (default: `~/.garminconnect`). The `Garmin` constructor accepts `tokenstore` and `tokenstore_base64` kwargs to override the path or supply base64-encoded tokens directly.
