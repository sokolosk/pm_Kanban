import os
import sqlite3
import secrets
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.environ.get("KANBAN_DB_PATH", DATA_DIR / "kanban.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            position INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            details TEXT DEFAULT '',
            position INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT
        );
        """,
    ]

    with _connect() as conn:
        for statement in queries:
            conn.execute(statement)


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions(token, user_id) VALUES (?, ?)",
            (token, user_id),
        )
    return token


def delete_session(token: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT users.* FROM sessions JOIN users ON sessions.user_id = users.id WHERE sessions.token = ?",
            (token,),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def create_user(username: str, password: str) -> Dict[str, Any]:
    password_hash = _hash_password(password)
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        user_id = cursor.lastrowid
    return {
        "id": user_id,
        "username": username,
        "password_hash": password_hash,
    }


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if user and user["password_hash"] == _hash_password(password):
        return user
    return None


def _serialize_board(board_row: sqlite3.Row) -> Dict[str, Any]:
    board_id = board_row["id"]
    with _connect() as conn:
        columns_rows = conn.execute(
            "SELECT * FROM columns WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()
        cards_rows = conn.execute(
            """
            SELECT * FROM cards
            WHERE column_id IN (
                SELECT id FROM columns WHERE board_id = ?
            )
            ORDER BY position
            """,
            (board_id,),
        ).fetchall()

    cards_by_column: Dict[int, List[sqlite3.Row]] = {}
    cards_map: Dict[str, Dict[str, Any]] = {}
    for card in cards_rows:
        cards_by_column.setdefault(card["column_id"], []).append(card)
        card_id = f"card-{card['id']}"
        cards_map[card_id] = {
            "id": card_id,
            "title": card["title"],
            "details": card["details"],
        }

    columns_payload = []
    for column in columns_rows:
        column_id = f"col-{column['id']}"
        card_ids = [
            f"card-{card['id']}"
            for card in cards_by_column.get(column["id"], [])
        ]
        columns_payload.append(
            {
                "id": column_id,
                "title": column["title"],
                "cardIds": card_ids,
            }
        )

    return {
        "id": f"board-{board_row['id']}",
        "title": board_row["title"],
        "columns": columns_payload,
        "cards": cards_map,
        "user_id": board_row["user_id"],
    }


def get_board(board_id: str | int) -> Optional[Dict[str, Any]]:
    board_pk = _resolve_board_id(board_id)
    with _connect() as conn:
        row = conn.execute("SELECT * FROM boards WHERE id = ?", (board_pk,)).fetchone()
    if not row:
        return None
    return _serialize_board(row)


def get_user_boards(user_id: int) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM boards WHERE user_id = ? ORDER BY sort_order, id", (user_id,)).fetchall()
    return [_serialize_board(row) for row in rows]


def create_board(user_id: int, title: str) -> Dict[str, Any]:
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO boards(user_id, title) VALUES (?, ?)",
            (user_id, title),
        )
        board_id = cursor.lastrowid
        _insert_default_columns(conn, board_id)
    return get_board(board_id)  # type: ignore


def save_board_state(board_id: str, board_data: Dict[str, Any]) -> Dict[str, Any]:
    board_pk = _resolve_board_id(board_id)
    with _connect() as conn:
        result = conn.execute(
            "UPDATE boards SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (board_data.get("title", "Untitled Board"), board_pk),
        )
        if result.rowcount == 0:
            raise ValueError("Board not found")
        column_ids = [row[0] for row in conn.execute("SELECT id FROM columns WHERE board_id = ?", (board_pk,)).fetchall()]
        if column_ids:
            conn.execute(
                f"DELETE FROM cards WHERE column_id IN ({','.join(['?']*len(column_ids))})",
                column_ids,
            )
        conn.execute("DELETE FROM columns WHERE board_id = ?", (board_pk,))

        for position, column in enumerate(board_data.get("columns", [])):
            cursor = conn.execute(
                "INSERT INTO columns(board_id, title, position) VALUES (?, ?, ?)",
                (board_pk, column.get("title", "Column"), position),
            )
            column_db_id = cursor.lastrowid
            for idx, card_id in enumerate(column.get("cardIds", [])):
                card = board_data.get("cards", {}).get(card_id)
                if not card:
                    continue
                conn.execute(
                    "INSERT INTO cards(column_id, title, details, position) VALUES (?, ?, ?, ?)",
                    (column_db_id, card.get("title", "Card"), card.get("details", ""), idx),
                )

    saved = get_board(board_pk)
    if not saved:
        raise ValueError("Board save failed")
    return saved


def ensure_default_user() -> int:
    user = get_user_by_username("user")
    if user:
        _ensure_sample_board(user["id"])
        return user["id"]

    user = create_user("user", "password")
    _ensure_sample_board(user["id"])
    return user["id"]


def _ensure_sample_board(user_id: int) -> None:
    boards = get_user_boards(user_id)
    if boards:
        return
    _create_sample_board(user_id)


def _create_sample_board(user_id: int) -> None:
    initial_data = {
        "title": "Kanban Studio",
        "columns": [
            ("Backlog", [
                ("Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
                ("Gather customer signals", "Review support tags, sales notes, and churn feedback."),
            ]),
            ("Discovery", [
                ("Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
            ]),
            ("In Progress", [
                ("Refine status language", "Standardize column labels and tone across the board."),
                ("Design card layout", "Add hierarchy and spacing for scanning dense lists."),
            ]),
            ("Review", [
                ("QA micro-interactions", "Verify hover, focus, and loading states."),
            ]),
            ("Done", [
                ("Ship marketing page", "Final copy approved and asset pack delivered."),
                ("Close onboarding sprint", "Document release notes and share internally."),
            ]),
        ],
    }

    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO boards(user_id, title) VALUES (?, ?)",
            (user_id, initial_data["title"]),
        )
        board_id = cursor.lastrowid
        for position, (title, cards) in enumerate(initial_data["columns"]):
            col_cursor = conn.execute(
                "INSERT INTO columns(board_id, title, position) VALUES (?, ?, ?)",
                (board_id, title, position),
            )
            column_id = col_cursor.lastrowid
            for idx, (card_title, details) in enumerate(cards):
                conn.execute(
                    "INSERT INTO cards(column_id, title, details, position) VALUES (?, ?, ?, ?)",
                    (column_id, card_title, details, idx),
                )


def _insert_default_columns(conn: sqlite3.Connection, board_id: int) -> None:
    default_columns = ["Backlog", "Discovery", "In Progress", "Review", "Done"]
    for idx, title in enumerate(default_columns):
        conn.execute(
            "INSERT INTO columns(board_id, title, position) VALUES (?, ?, ?)",
            (board_id, title, idx),
        )


def _resolve_board_id(board_id: str | int) -> int:
    if isinstance(board_id, int):
        return board_id
    if isinstance(board_id, str) and board_id.startswith("board-"):
        return int(board_id.split("-", 1)[1])
    return int(board_id)


init_db()
ensure_default_user()