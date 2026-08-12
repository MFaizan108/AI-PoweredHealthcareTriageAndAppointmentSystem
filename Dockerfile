FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directories that get volume-mounted at runtime (staticfiles, media) must be writable by the
# non-root user *before* Docker copies them into the named volumes on first mount, or collectstatic
# and file uploads fail with a permission error once the container actually runs as appuser.
# A real home directory (not --no-create-home) is required too: gunicorn 26's control-server
# feature writes a socket under $HOME on startup and logs a (non-fatal, but noisy) permission
# error on every boot without one.
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "ai_healthcare_triage_appointment_system.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
