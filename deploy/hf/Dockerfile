# Single-container build for Hugging Face Spaces (SDK: docker, app_port: 7860).
# Builds the React frontend, then serves it from FastAPI via StaticFiles.
# Build context = the Space repo root (must contain backend/, scripts/,
# main.py, frontend/, data/ — see docs/DEPLOY_HF_SPACES.md).

# ---------- Stage 1: build the frontend ----------
FROM node:22-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci || npm install
COPY frontend ./
RUN npm run build

# ---------- Stage 2: Python runtime ----------
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Application code
COPY backend /app/backend
COPY scripts /app/scripts
COPY main.py /app/main.py

# Locally-acquired evidence data (Delhi derived products, event catalog).
# In the Space repo these travel via Git LFS.
COPY data /app/data

# Built frontend served by FastAPI at "/"
COPY --from=frontend-build /build/dist /app/frontend/dist

# HF Spaces runs containers as non-root uid 1000.
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
