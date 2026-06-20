FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GARMINTOKENS=/data/tokens

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY docker/app/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Install the local garminconnect source (overrides PyPI version with the
# fork's fixes from this repo).
COPY garminconnect /tmp/garminconnect-src/garminconnect
COPY pyproject.toml README.md /tmp/garminconnect-src/
RUN pip install /tmp/garminconnect-src \
 && rm -rf /tmp/garminconnect-src

COPY docker/app /app

RUN useradd --create-home --uid 1000 dash \
 && mkdir -p /data/tokens /data/cache \
 && chown -R dash:dash /data /app
USER dash

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
