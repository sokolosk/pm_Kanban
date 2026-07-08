import importlib
import json
import sys
from typing import AsyncIterator
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport
@pytest.fixture()
def test_app(monkeypatch, tmp_path) -> FastAPI:
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("KANBAN_DB_PATH", str(db_path))

    for module in ["main", "routes", "routes.ai", "routes.ai_chat", "routes.kanban", "database"]:
        sys.modules.pop(module, None)

    main_module = importlib.import_module("main")
    app = main_module.app
    app.dependency_overrides.clear()
    app.state.ai_module = main_module.ai
    app.state.ai_chat_module = main_module.ai_chat
    app.state.database_module = importlib.import_module("database")
    return app


@pytest.fixture()
def test_client(test_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = ASGITransport(app=test_app)
    async_client = httpx.AsyncClient(transport=transport, base_url="http://test")

    try:
        yield async_client
    finally:
        import anyio

        anyio.run(async_client.aclose)


@pytest.mark.asyncio
async def test_ai_test_endpoint_success(test_app, test_client):
    mock_client = AsyncMock()
    mock_client.math_connectivity_test.return_value = "4"

    ai_module = test_app.state.ai_module
    test_app.dependency_overrides[ai_module.get_ai_client] = lambda: mock_client
    try:
        response = await test_client.post("/api/ai/test")
    finally:
        test_app.dependency_overrides.pop(ai_module.get_ai_client, None)

    assert mock_client.math_connectivity_test.called
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"result": "4"}
    mock_client.math_connectivity_test.assert_awaited_once()


@pytest.mark.asyncio
async def test_ai_chat_without_board_update(test_app, test_client):
    database = test_app.state.database_module
    user_id = database.ensure_default_user()
    board = database.get_user_boards(user_id)[0]

    mock_client = AsyncMock()
    mock_client.chat_completion.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "assistant_response": "Here is your update.",
                        }
                    )
                }
            }
        ]
    }

    ai_chat_module = test_app.state.ai_chat_module
    test_app.dependency_overrides[ai_chat_module.get_ai_client] = lambda: mock_client
    try:
        response = await test_client.post(
            "/api/ai/chat",
            json={
                "board": board,
                "message": "Summarize the board",
                "history": [],
            },
        )
    finally:
        test_app.dependency_overrides.pop(ai_chat_module.get_ai_client, None)

    payload = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert payload == {"reply": "Here is your update.", "board": None, "board_updated": False}
    mock_client.chat_completion.assert_awaited_once()


@pytest.mark.asyncio
async def test_ai_chat_with_board_update(test_app, test_client):
    database = test_app.state.database_module
    user_id = database.ensure_default_user()
    board = database.get_user_boards(user_id)[0]
    updated_board = {
        **board,
        "title": "Kanban Studio (AI)",
    }

    mock_client = AsyncMock()
    mock_client.chat_completion.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "assistant_response": "Renamed the board for clarity.",
                            "board_update": updated_board,
                        }
                    )
                }
            }
        ]
    }

    ai_chat_module = test_app.state.ai_chat_module
    test_app.dependency_overrides[ai_chat_module.get_ai_client] = lambda: mock_client
    try:
        response = await test_client.post(
            "/api/ai/chat",
            json={
                "board": board,
                "message": "Rename the board",
                "history": [],
            },
        )
    finally:
        test_app.dependency_overrides.pop(ai_chat_module.get_ai_client, None)

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["board_updated"] is True
    assert payload["reply"] == "Renamed the board for clarity."
    assert payload["board"]["title"] == "Kanban Studio (AI)"

    db_board = database.get_board(board["id"])
    assert db_board["title"] == "Kanban Studio (AI)"
    mock_client.chat_completion.assert_awaited_once()

