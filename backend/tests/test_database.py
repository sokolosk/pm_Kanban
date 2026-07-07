import sqlite3
from pathlib import Path

import pytest


@pytest.fixture()
def db_module(monkeypatch, tmp_path):
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("KANBAN_DB_PATH", str(db_path))

    import importlib
    import sys

    backend_root = Path(__file__).resolve().parent.parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    module = importlib.import_module("database")
    module = importlib.reload(module)
    module.DB_PATH = Path(db_path)
    module.init_db()
    module.ensure_default_user()
    return module


def test_init_db_creates_tables_and_seed_data(db_module):
    with sqlite3.connect(db_module.DB_PATH) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    expected = {"users", "boards", "columns", "cards", "sessions"}
    assert expected.issubset(tables)

    user = db_module.get_user_by_username("user")
    assert user is not None


def test_board_crud_flow(db_module):
    user = db_module.create_user("alice", "secret")
    board = db_module.create_board(user["id"], "Project X")

    assert len(board["columns"]) == 5

    temp_card_id = "card-new"
    board["cards"][temp_card_id] = {
        "id": temp_card_id,
        "title": "Write spec",
        "details": "Document requirements",
    }
    board["columns"][0]["cardIds"].append(temp_card_id)
    board["title"] = "Project X Updated"

    saved = db_module.save_board_state(board["id"], board)
    assert saved["title"] == "Project X Updated"
    first_column_cards = saved["columns"][0]["cardIds"]
    assert len(first_column_cards) == 1
    saved_card = saved["cards"][first_column_cards[0]]
    assert saved_card["title"] == "Write spec"
    assert saved_card["details"] == "Document requirements"


def test_authentication_and_sessions(db_module):
    user = db_module.create_user("bob", "password123")
    assert db_module.authenticate_user("bob", "password123")
    assert db_module.authenticate_user("bob", "wrong") is None

    token = db_module.create_session(user["id"])
    fetched = db_module.get_user_by_token(token)
    assert fetched is not None
    assert fetched["username"] == "bob"

    db_module.delete_session(token)
    assert db_module.get_user_by_token(token) is None


def test_error_handling_for_missing_records(db_module):
    assert db_module.get_board("board-99999") is None

    with pytest.raises(ValueError):
        db_module.save_board_state(
            "board-99999",
            {
                "title": "Ghost",
                "columns": [],
                "cards": {},
            },
        )
