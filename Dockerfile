# ---- Stage 1: Build NextJS frontend ----
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# ---- Stage 2: Python backend with uv ----
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy backend source
COPY backend/pyproject.toml ./backend/
COPY backend/ ./backend/

# Install Python dependencies
WORKDIR /app/backend
RUN uv sync --no-dev

# Copy built frontend
COPY --from=frontend-builder /app/frontend/out /app/backend/static

# Expose port
EXPOSE 8000

# Run uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]