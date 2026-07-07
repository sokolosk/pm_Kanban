import importlib
import sys
from typing import AsyncIterator
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport

from ai import OpenRouterError


@pytest.fixture()
def test_app(monkeypatch, tmp_path) -> FastAPI:
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("KANBAN_DB_PATH", str(db_path))

    for module in ["main", "routes.ai", "routes.kanban", "database"]:
        sys.modules.pop(module, None)

    main_module = importlib.import_module("main")
    app = main_module.app
    app.dependency_overrides.clear()
    app.state.ai_module = main_module.ai  # share the exact module instance used by the router
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

