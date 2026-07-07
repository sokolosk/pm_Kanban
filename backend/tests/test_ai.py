import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from main import app


@pytest.mark.asyncio
async def test_ai_test_endpoint_success():
    mock_client = AsyncMock()
    mock_client.math_connectivity_test.return_value = "4"

    with patch("routes.ai.OpenRouterClient", return_value=mock_client):
        async with AsyncClient(app=app, base_url="http://test") as async_client:
            response = await async_client.post("/api/ai/test")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"result": "4"}
    mock_client.math_connectivity_test.assert_awaited_once()


@pytest.mark.asyncio
async def test_ai_test_endpoint_failure():
    with patch(
        "routes.ai.OpenRouterClient",
        return_value=AsyncMock(math_connectivity_test=AsyncMock(side_effect=Exception("boom"))),
    ):
        async with AsyncClient(app=app, base_url="http://test") as async_client:
            response = await async_client.post("/api/ai/test")

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    body = response.json()
    assert body["detail"] == "boom"
