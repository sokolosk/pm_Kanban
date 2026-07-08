# Code Review

Full-repo review of Kanban Studio (backend, frontend, infra, docs, tests). Findings are ordered by severity. Each includes location, impact, and a recommended action.

Scope: `backend/`, `frontend/src/`, `frontend/tests/`, `Dockerfile`, `docker-compose.yml`, `scripts/`, `docs/`.

## Summary

The codebase is small, readable, and mostly consistent with its own stated standards (simple, no speculative abstraction). Test coverage exists for the database layer, the AI routes, and the core frontend components. The most important gap is authentication: the AI endpoints bypass the auth system that the rest of the backend enforces, and one of them can write to any board by ID with no ownership check. That should be fixed before this goes anywhere beyond a local single-user demo.

| Severity | Count |
|---|---|
| Critical | 2 |
| High | 2 |
| Medium | 4 |
| Low | 6 |

---

## Critical

### C1. `POST /api/ai/chat` has no authentication and no board-ownership check
**File:** `backend/routes/ai_chat.py:132-175`

The route has no `Depends(get_current_user)` at all — unlike every route in `routes/kanban.py`. Anyone who can reach the backend (no bearer token required) can call this endpoint. Worse, the handler resolves `board_id` from the request body / AI response and calls `save_board_state(board_id, board_update)` directly, with **no check that the board belongs to any particular user**:

```python
board_id = board_update.get("id") or payload.board.get("id")
...
saved_board = save_board_state(board_id, board_update)
```

Board IDs are small sequential integers (`board-1`, `board-2`, ...). Any caller can pass an arbitrary `board.id` in the request payload and overwrite (or wipe, absent the validation added for C2/related fix) another user's board. This is a textbook IDOR, compounded by missing authentication.

Today's practical impact is limited because the MVP only ever provisions one hardcoded user, but the schema and `AGENTS.md` explicitly design for multiple users, and this bug will be live the moment a second account exists.

**Action:** Add `current_user: dict = Depends(get_current_user)` to `ai_chat`, and before saving, verify the target board belongs to `current_user["id"]` (reuse the ownership check pattern from `routes/kanban.py:107-112`).

### C2. `POST /api/ai/test` has no authentication
**File:** `backend/routes/ai.py:16-28`

Same missing-auth issue as C1, lower blast radius since it doesn't touch the database — but it does let an unauthenticated caller trigger real calls against your `OPENROUTER_API_KEY`, burning quota/cost with no login required.

**Action:** Add `Depends(get_current_user)` here too, unless there's a deliberate reason to keep a public health-style probe (in which case, rate-limit it).

---

## High

### H1. Session tokens never expire
**File:** `backend/database.py:69-90`, `98-104`

The `sessions` table has an `expires_at` column, but `create_session` never sets it and `get_user_by_token` never checks it:

```python
def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT users.* FROM sessions JOIN users ON sessions.user_id = users.id WHERE sessions.token = ?",
            (token,),
        ).fetchone()
    return dict(row) if row else None
```

A token is valid forever until the user explicitly logs out. Combined with the token being stored in `localStorage` (see L5), a leaked token has no natural expiry.

**Action:** Set `expires_at` on creation (e.g. 7–30 days) and reject/delete expired sessions in `get_user_by_token`.

### H2. `routes/kanban.py` has no test coverage
**File:** `backend/tests/` (no `test_kanban.py` exists)

`backend/tests/test_database.py` tests the DB layer directly; `backend/tests/test_ai.py` tests the AI routes. Nothing exercises `routes/kanban.py` over HTTP: no test for login success/failure, 401 on a missing/invalid token, 403 on cross-user board access, or the full board GET/PUT round trip. This is precisely the code that enforces authorization — and C1 shows how easily an authorization gap can slip through unnoticed when the surrounding code has no tests to contrast it against.

**Action:** Add `backend/tests/test_kanban.py` covering: login with correct/incorrect credentials, accessing a protected route without/with an invalid token, a user attempting to GET/PUT another user's board (expect 403), and a normal create → get → update round trip.

---

## Medium

### M1. Column rename fires a network request on every keystroke
**File:** `frontend/src/components/KanbanColumn.tsx:42-47`, `frontend/src/components/KanbanBoard.tsx:99-110`

```tsx
<input
  value={column.title}
  onChange={(event) => onRename(column.id, event.target.value)}
  ...
/>
```

`onRename` → `handleRenameColumn` → `persistBoard` fires a `PUT /api/boards/{id}` on every single keystroke. Typing "Ideas" sends 5 separate save requests. Beyond the wasted requests, this creates a real race: `persistBoard` unconditionally does `setBoard(saved)` with whatever the server echoes back, so if an earlier request resolves *after* a later one (plausible under any latency variance), a stale server response can overwrite the user's most recent keystrokes on screen.

**Action:** Debounce the persisted save (e.g. 400-600ms after the last keystroke), or persist on blur, while keeping local state updates immediate for responsiveness.

### M2. No protection against out-of-order save responses
**File:** `frontend/src/components/KanbanBoard.tsx:56-67`

`persistBoard` has no request sequencing — every call to `saveBoard` independently resolves and calls `setBoard(saved)`. Drag-and-drop, add-card, and delete-card can all fire close together (see M1 for rename specifically), and there's nothing to prevent an older in-flight response from clobbering newer local state.

**Action:** Track a monotonically increasing request id (or use `AbortController` to cancel superseded requests) and ignore responses that aren't the latest.

### M3. Passwords hashed with unsalted SHA-256
**File:** `backend/database.py:15-16`

```python
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
```

Fine as a placeholder for today's single hardcoded `user`/`password` account, but `create_user` is a general-purpose function and the schema is explicitly designed for future multi-user support (`docs/DATABASE.md`). Unsalted SHA-256 is fast to brute-force and provides no protection against rainbow tables.

**Action:** Before real user registration ships, switch to `bcrypt` or `argon2` (e.g. via `passlib`).

### M4. `save_board_state` fully deletes and reinserts every column/card on every save
**File:** `backend/database.py:220-255`

Every save — a drag-and-drop move, a rename, an AI edit — deletes *all* of a board's columns and cards and reinserts them from the payload:

```python
conn.execute(f"DELETE FROM cards WHERE column_id IN (...)", column_ids)
conn.execute("DELETE FROM columns WHERE board_id = ?", (board_pk,))
for position, column in enumerate(board_data.get("columns", [])):
    cursor = conn.execute("INSERT INTO columns(...) VALUES (...)", ...)
    ...
```

This means: (1) every card/column gets a **new autoincrement ID** on every unrelated edit, so any external reference to an ID is invalidated constantly; (2) `created_at` timestamps are lost and reset on every save; (3) it's wasteful — moving one card rewrites the entire board's row set.

**Action:** Diff the incoming board against the existing rows and only insert/update/delete what actually changed. This is more work than the current approach but removes an entire class of "why did this ID change" bugs, and is also what makes M2's out-of-order race safe to reason about.

---

## Low

### L1. SQLite connections are never explicitly closed
**File:** `backend/database.py:19-23` (`_connect`, used throughout the file)

```python
def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    ...
    return conn
```

Every helper function opens a brand-new connection and uses `with _connect() as conn:` — but Python's `sqlite3.Connection` context manager only commits/rolls back the transaction, it does **not** close the connection. Connections are left for garbage collection. Not a problem at today's local, single-process scale, but a latent resource leak if this ever runs under real concurrent load.

**Action:** Wrap in `try/finally: conn.close()`, or centralize connection handling in one place.

### L2. No retry around OpenRouter calls
**File:** `backend/ai.py:41-64`

During manual testing this session, a chat request to OpenRouter returned a transient `502 Bad Gateway`, which surfaced immediately as a user-facing error with no retry. `openrouter/free` is a free/shared-capacity endpoint and this kind of flakiness should be expected in normal operation.

**Action:** Add a small retry with backoff (2-3 attempts) for transient network errors / 5xx responses in `OpenRouterClient.chat_completion`.

### L3. Drag listeners cover the entire card, including the Remove button
**File:** `frontend/src/components/KanbanCard.tsx:20-31`

```tsx
<article ref={setNodeRef} style={style} ... {...attributes} {...listeners}>
  ...
  <button onClick={() => onDelete(card.id)}>Remove</button>
</article>
```

`{...listeners}` (dnd-kit's pointer handlers) is spread across the whole card, including the interactive Remove button nested inside it. This is a known dnd-kit footgun in real browsers: pointer-down on the button can be captured by the drag sensor before the click registers, making delete occasionally unreliable. jsdom-based tests won't catch this since they don't replicate real pointer capture behavior.

**Action:** Restrict `{...listeners}` to a dedicated drag handle (e.g. a small grip icon), or call `event.stopPropagation()` on the Remove button's pointer-down.

### L4. Stray manual debug script committed to the repo
**File:** `frontend/login-test.ps1`

A one-off, assertion-free PowerShell script that logs in and prints the response. It's not referenced by `npm run test:unit` or `test:e2e`, is Windows-only, and reads as leftover scratch work from Part 7 rather than a maintained artifact.

**Action:** Delete it, or move it to a clearly-labeled `dev/` scratch folder if it's genuinely useful for manual debugging.

### L5. Session token stored in `localStorage`
**File:** `frontend/src/app/page.tsx:14-20, 30-31`

Acceptable for this MVP's threat model today (React auto-escapes all rendered content, no `dangerouslySetInnerHTML` anywhere in the codebase, so there's no first-party XSS vector), but worth flagging because it compounds H1: a token that never expires and is readable by any script on the page has no real ceiling on exposure if that ever changes (e.g. a future dependency with an XSS bug).

**Action:** Low priority given current scope; revisit if the app grows a public-facing surface or adds third-party scripts. An httpOnly cookie would remove the risk entirely.

### L6. `docs/PLAN.md` checkboxes don't reflect reality
**File:** `docs/PLAN.md`

Parts 4 through 10 are all shown unchecked, and Part 5 still says "awaiting sign-off" / "Pending Sign-off," even though git history (`Part 7 complete`, `Part 8 complete` ×2, `Part 10 complete`) and the actual code confirm all ten parts are implemented. Since this file is the project's working plan/checklist, letting it drift from reality undermines its usefulness for anyone (including a future agent) trying to figure out what's actually done.

**Action:** Update the checkboxes to match shipped work, or note in the file that it's superseded by `CLAUDE.md` / git history for status tracking.

---

## Also noted, not actioned

- **AI board-update architecture is inherently fragile.** This session's earlier fix (`_is_valid_board_update` in `routes/ai_chat.py`) guards against the *obviously* malformed case (missing columns/cards) that was observed wiping a board. It does not protect against a structurally valid but semantically wrong response (e.g. the model hallucinating a card's contents while keeping the JSON shape intact) — because the whole design asks the model to regenerate and echo back the *entire* board rather than expressing a targeted change. A more robust long-term design would have the AI emit discrete operations (`rename_column`, `add_card`, `move_card`, ...) that get validated and applied individually, rather than a full-board replace. Flagging as a future architecture improvement, not a bug to fix now.
- **Docker hardening**: no `HEALTHCHECK` in `Dockerfile`/`docker-compose.yml` despite `/api/health` existing, and the container runs as root (no `USER` directive). Minor, worth doing before any real deployment.
- Parameterized SQL is used correctly everywhere, including the one place that looks suspicious at a glance (`save_board_state`'s dynamic `IN (...)` placeholder generation in `backend/database.py:229-234` — the interpolated part is only the *count* of `?` placeholders, built from internal integer IDs, not user input).
- No XSS surface found (no `dangerouslySetInnerHTML`, no raw HTML injection).
- `.env` / `.env.local` are correctly gitignored in both the root and `frontend/` gitignore files; only `.env.example` is tracked.

## Suggested priority order

1. C1, C2 — wire up auth on the AI routes (small, high-impact fix).
2. H2 — add `test_kanban.py` so the auth surface has coverage going forward.
3. H1 — session expiry.
4. M3 — password hashing, before any real user signs up.
5. M1/M2 — debounce + response-ordering guard on board saves.
6. M4, L1-L6 — as time allows; none are urgent.
