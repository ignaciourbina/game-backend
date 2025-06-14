# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

# Keep images tidy and logs unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source tree (app.py, game_db.py, etc.)
COPY . .

# Hugging Face mounts a persistent volume at /data – create it and make it writable
RUN mkdir -p /data && chmod 777 /data

# HF will pass the port in $PORT; default to 7860 for local builds
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
