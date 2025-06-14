# ---------------- Dockerfile ----------------
# syntax=docker/dockerfile:1
#
# Use this **only** for a Docker Space.  For a FastAPI Space you can delete it.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite persistent volume provided by HF is mounted at /data
RUN mkdir -p /data && chmod 777 /data

# Hugging Face assigns a port in $PORT (default 7860 locally)
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]

# ---------------- requirements.txt ----------------
fastapi==0.111.0
uvicorn[standard]==0.29.0
