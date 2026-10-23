FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend
WORKDIR /app
COPY backend/requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && groupadd --gid 10001 t44 && useradd --uid 10001 --gid t44 --no-create-home t44
COPY backend/ /app/backend/
COPY specs/database/ /app/specs/database/
COPY specs/contracts/ /app/specs/contracts/
COPY deployment/runtime_probe.py /app/deployment/runtime_probe.py
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "t44.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--no-access-log", "--no-proxy-headers"]
