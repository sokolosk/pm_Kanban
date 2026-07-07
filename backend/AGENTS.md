# Backend - Kanban Studio API

Python FastAPI backend for the Kanban Studio MVP.

## Structure

- `main.py` - FastAPI application entry point, serves static frontend and API routes
- `pyproject.toml` - Python project config with uv as package manager
- `static/` - Directory containing the built frontend (copied from frontend/out at build time)
- `data/` - Runtime directory for SQLite database (created on first run)

## Key decisions

- Uses `uv` for Python package management
- Static NextJS frontend is served from `static/` at `/`
- API routes are under `/api/`
- SQLite database stored in `data/kanban.db`