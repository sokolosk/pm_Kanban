# High level steps for project

Part 1: Plan

Enrich this document to plan out each of these parts in detail, with substeps listed out as a checklist to be checked off by the agent, and with tests and success critieria for each. Also create an AGENTS.md file inside the frontend directory that describes the existing code there. Ensure the user checks and approves the plan.

Part 2: Scaffolding ✅

Set up the Docker infrastructure, the backend in backend/ with FastAPI, and write the start and stop scripts in the scripts/ directory. This should serve example static HTML to confirm that a 'hello world' example works running locally and also make an API call.

**Completed:**
- [x] Created `backend/main.py` with FastAPI app + health endpoint `/api/health`
- [x] Created `backend/pyproject.toml` with uv as package manager
- [x] Created `backend/static/index.html` — static test page with API health checker
- [x] Created `Dockerfile` — multi-stage build (Node 22 -> frontend build, Python 3.12 -> serve)
- [x] Created `docker-compose.yml` — single service with volume for database
- [x] Created `.env` / `.env.example` / `.dockerignore`
- [x] Created `scripts/start.sh`, `scripts/stop.sh`, `scripts/start.bat`, `scripts/stop.bat`
- [x] Updated `backend/AGENTS.md` and `scripts/AGENTS.md`
- [x] Updated `frontend/next.config.ts` — static export config (`output: "export"`)
- [x] Updated `.gitignore` — added node_modules, .next, out, backend/data, .env
- [x] **Tested:** `docker compose build` succeeds, container starts, `GET /api/health` returns `{"status":"ok"}`, root `/` serves the built frontend

Part 3: Add in Frontend ✅

Now update so that the frontend is statically built and served, so that the app has the demo Kanban board displayed at /. Comprehensive unit and integration tests.

**Status:** Frontend already built. Unit tests (`vitest`) and E2E tests (`playwright`) exist. The Docker multi-stage build compiles the frontend and copies it to the backend's static directory.

Part 4: Add in a fake user sign in experience

Now update so that on first hitting /, you need to log in with dummy credentials ("user", "password") in order to see the Kanban, and you can log out. Comprehensive tests.

- [ ] Add login page component (`LoginForm.tsx`)
- [ ] Add auth context/state management (`AuthContext.tsx` or simple hook)
- [ ] Wrap the KanbanBoard in ProtectedRoute / auth gate
- [ ] Login form validates against hardcoded "user" / "password"
- [ ] "Logout" button to return to login screen
- [ ] No backend API call needed — purely frontend auth
- [ ] Unit tests: renders login when not authenticated, shows Kanban after login, logout returns to login
- [ ] E2E tests: login flow, invalid credentials, logout flow

Part 5: Database modeling (awaiting sign-off)

Now propose a database schema for the Kanban, using a normalized SQLite database (per AGENTS.md). Document the schema in docs/ and get explicit user approval before implementing Part 6.

- [x] Design SQLite schema (tables: users, boards, columns, cards, sessions)
- [x] Document schema + ERD + sample SQL in `docs/DATABASE.md`
- [x] Outline how upcoming API routes will read/write the schema
- [ ] User sign-off required before implementing Part 6

Part 6: Backend

Now add API routes to allow the backend to read and change the Kanban for a given user; test this thoroughly with backend unit tests. The database should be created if it doesn't exist.

- [ ] Add `backend/database.py` with JSON file read/write logic
- [ ] Add `backend/routes/` folder with kanban CRUD endpoints
- [ ] API: `GET /api/boards/{user_id}` — load board
- [ ] API: `PUT /api/boards/{user_id}` — save board
- [ ] API: `POST /api/login` — validate credentials, return token/session
- [ ] Database auto-created on first access
- [ ] Backend tests with pytest: database initialization, CRUD operations
- [ ] Backend tests: error handling (user not found, invalid data)

Part 7: Frontend + Backend

Now have the frontend actually use the backend API, so that the app is a proper persistent Kanban board. Test very throughly.

- [ ] Create `frontend/src/lib/api.ts` — API client functions
- [ ] Update KanbanBoard to load/save state via API on mount and after changes
- [ ] Add loading and error states for API calls
- [ ] Wire login to backend endpoint
- [ ] Unit tests: API client mock, board load/save, login/logout flow
- [ ] E2E tests: full login -> view board -> add card -> reload -> card persists

Part 8: AI connectivity

Now allow the backend to make an AI call via OpenRouter. Test connectivity with a simple "2+2" test and ensure the AI call is working.

- [ ] Add `backend/ai.py` with OpenRouter client
- [ ] Add `POST /api/ai/test` — simple 2+2 test endpoint
- [ ] Test with `curl` or pytest that AI responds
- [ ] Add proper error handling for API key missing or call failure
- [ ] Backend tests: mock the AI call, verify response format

Part 9: Now extend the backend call so that it always calls the AI with the JSON of the Kanban board, plus the user's question (and conversation history). The AI should respond with Structured Outputs that includes the response to the user and optionaly an update to the Kanban. Test thoroughly.

- [ ] Define Pydantic models for structured output (response text + optional board update)
- [ ] Add `POST /api/ai/chat` endpoint accepting: board JSON, user message, conversation history
- [ ] Forward system prompt + board JSON + history to OpenRouter with structured output
- [ ] Parse structured response; if board update included, apply it
- [ ] Return structured result to frontend
- [ ] Backend tests: mock AI, verify structured output parsing, verify board update flow

Part 10: Now add a beautiful sidebar widget to the UI supporting full AI chat, and allowing the LLM (as it determines) to update the Kanban based on its Structured Outputs. If the AI updates the Kanban, then the UI should refresh automatically.

- [ ] Create `AIChatSidebar.tsx` — collapsible sidebar component
- [ ] Create `AIChatMessage.tsx` — message bubble component
- [ ] Add chat input at the bottom of the sidebar
- [ ] Wire to `POST /api/ai/chat` with board context + conversation history
- [ ] On AI response, if board update included, merge into Kanban state
- [ ] Auto-refresh Kanban board when AI updates the data
- [ ] Unit tests: sidebar rendering, send message, receive response, board update
- [ ] E2E tests: open sidebar -> send message -> receive AI reply -> board updates
- [ ] Visual: beautiful matching the existing color scheme (yellow/blue/purple/navy)