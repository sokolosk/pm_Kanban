# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Kanban Studio: a single-board Kanban MVP with an AI chat sidebar that can read and edit the board. NextJS frontend, Python FastAPI backend, SQLite database, packaged as one Docker container (backend serves the frontend's static export at `/`). AI calls go through OpenRouter (`openrouter/free` model).

Full requirements/decisions: `AGENTS.md` (root). Backend-specific notes: `backend/AGENTS.md`. Scripts notes: `scripts/AGENTS.md`. Build progress and phased checklist: `docs/PLAN.md`. DB schema/ERD: `docs/DATABASE.md`.

## Commands

### Frontend (`frontend/`)
```bash
npm install
npm run dev              # Next dev server on :3000
npm run build             # static export to frontend/out (output: "export")
npm run lint
npm run test:unit         # vitest run
npm run test:unit:watch   # vitest watch
npm run test:e2e          # playwright (auto-starts dev server on :3000)
npm run test:all          # unit then e2e
```
Run a single vitest file: `npx vitest run src/components/KanbanBoard.test.tsx`
Run a single playwright test: `npx playwright test tests/<file>.spec.ts -g "test name"`

### Backend (`backend/`)
Uses `uv` as the package manager.
```bash
uv sync
uv run uvicorn main:app --reload --port 8000
uv run pytest                          # all tests (testpaths = tests)
uv run pytest tests/test_ai.py -k name # single test
```

### Docker (full stack)
```bash
scripts\start.bat   # Windows — builds/runs docker-compose, app at http://localhost:8000
scripts\stop.bat
```
`docker-compose run --rm app uv run pytest` is the intended way to run backend tests inside the container per `docs/DATABASE.md`.

## Architecture

**Build/serve model**: The Dockerfile is a two-stage build — Node builds the NextJS static export (`frontend/out`), which is copied into `backend/static/` and served by FastAPI at `/`. In local dev, frontend (`:3000`) and backend (`:8000`) run separately; the frontend calls the backend via `NEXT_PUBLIC_API_BASE` (empty string in Docker since same-origin, set to `http://localhost:8000` for local dev against a separate backend).

**Backend structure** (`backend/`):
- `main.py` — FastAPI app, CORS for localhost:3000, mounts routers, serves `static/index.html` at `/`, health check at `/api/health`.
- `database.py` — all persistence. Raw `sqlite3` (no ORM). Owns schema creation (`init_db`), a default user/board seed (`ensure_default_user`), and board serialization: DB rows are shaped into the frontend's `BoardData` JSON (`{id, title, columns: [{id, title, cardIds}], cards: {id: {id, title, details}}}`) with prefixed IDs (`board-N`, `col-N`, `card-N`). `save_board_state` does a full delete-and-reinsert of a board's columns/cards on every save (not a diff/patch) — the whole board is always the unit of write.
- `routes/kanban.py` — auth (`/api/login`, `/api/logout` via bearer tokens in the `sessions` table) and board CRUD (`/api/boards/me`, `/api/boards/{id}`). `get_current_user` dependency enforces board ownership on every board route.
- `routes/ai.py` — `/api/ai/test`, a simple connectivity check.
- `routes/ai_chat.py` — `/api/ai/chat`: builds a message list (system prompt + history + board JSON + user question wrapped in `<context>`/`<question>` tags), calls OpenRouter with a JSON-schema structured output (`assistant_response`, optional `board_update`). If `board_update` is present, it's written straight through `save_board_state` — the AI can effectively rewrite the whole board. Both AI routers use a swappable `AI_CLIENT_FACTORY` module-level callable so tests can inject a fake client instead of mocking `httpx`.
- `ai.py` — `OpenRouterClient`, thin wrapper over `httpx` posting to OpenRouter's chat completions endpoint; raises `OpenRouterError` for missing key / HTTP failures.

**Database**: SQLite at `backend/data/kanban.db` (overridable via `KANBAN_DB_PATH` env var, used in Docker to point at a volume). Schema: `users` → `boards` → `columns` → `cards`, plus `sessions` for bearer tokens. MVP is single-board-per-user but schema supports multiple boards/users. See `docs/DATABASE.md` for the full ERD; keep it in sync with `database.py`'s `init_db` if the schema changes.

**Frontend structure** (`frontend/src/`):
- `lib/kanban.ts` — `BoardData`/`Column`/`Card` types (the shared board shape with the backend) and pure board-transform logic (`moveCard` drag-and-drop reordering across/within columns, `createId`).
- `lib/api.ts` — fetch wrappers for every backend endpoint (`apiLogin`, `apiLogout`, `fetchBoards`, `saveBoard`, `aiChat`), all bearer-token authenticated, using `NEXT_PUBLIC_API_BASE`.
- `components/KanbanBoard.tsx` — top-level board state owner. Loads the board on mount via `fetchBoards`, and every mutation (drag/drop, rename column, add/delete card) updates local state optimistically then calls `persistBoard` → `saveBoard` to push the full board back to the backend. Renders `KanbanColumn`s inside a `@dnd-kit` `DndContext`, plus the `AIChatSidebar`.
- `components/AIChatSidebar.tsx` — chat UI that calls `aiChat`; when the response includes a board, calls `onBoardUpdate` so `KanbanBoard` replaces its state (this is how AI-driven board edits reach the UI).
- Auth is currently a frontend-only gate (`LoginForm.tsx` + login state in `page.tsx`) even though the backend has real session-token auth in place — see the "Auth alignment" note in `docs/DATABASE.md` for the intended transition.

## Coding standards (from `AGENTS.md`)

- Use latest/idiomatic versions of libraries.
- Keep it simple — no over-engineering, no unnecessary defensive programming, no speculative features.
- Be concise; no emojis, ever.
- When debugging, find root cause with evidence before fixing — don't guess.
- Color scheme (Tailwind CSS vars): Accent Yellow `#ecad0a`, Blue Primary `#209dd7`, Purple Secondary `#753991`, Dark Navy `#032147`, Gray Text `#888888`.

## Notes for future work

`docs/PLAN.md` tracks phased delivery (Parts 1–10) with checkboxes — check it before starting new feature work to see what's already done vs. planned next, and update it as parts complete.
