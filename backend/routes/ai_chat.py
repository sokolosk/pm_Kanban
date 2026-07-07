from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ai import OpenRouterClient, OpenRouterError
from database import save_board_state

router = APIRouter(prefix="/api/ai", tags=["ai"])

AI_CLIENT_FACTORY: Callable[[], OpenRouterClient] = OpenRouterClient

SYSTEM_PROMPT = (
    "You are an expert project management assistant embedded into a Kanban app. "
    "Always respond with JSON using the provided schema. "
    "Write a concise helpful reply for the user in `assistant_response`. "
    "If you need to update the board, include a complete board JSON in `board_update`."
)

STRUCTURED_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "kanban_ai_response",
        "schema": {
            "type": "object",
            "properties": {
                "assistant_response": {
                    "type": "string",
                    "description": "Message to display to the user",
                },
                "board_update": {
                    "type": "object",
                    "description": "Full Kanban board JSON after applying the requested changes",
                },
            },
            "required": ["assistant_response"],
            "additionalProperties": False,
        },
    },
}


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIChatRequest(BaseModel):
    board: dict[str, Any]
    message: str
    history: list[ConversationMessage] = Field(default_factory=list)


class AIChatResponse(BaseModel):
    reply: str
    board: dict[str, Any] | None = None
    board_updated: bool = False


class AIChatErrorResponse(BaseModel):
    detail: str


def get_ai_client() -> OpenRouterClient:
    return AI_CLIENT_FACTORY()


def _build_messages(payload: AIChatRequest) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    for entry in payload.history:
        messages.append(entry.model_dump())

    user_content = (
        "<context>\n"
        "Board JSON: "
        f"{json.dumps(payload.board, ensure_ascii=False)}\n"
        "</context>\n"
        "<question>\n"
        f"{payload.message}\n"
        "</question>"
    )
    messages.append({"role": "user", "content": user_content})
    return messages


def _parse_response(raw: dict[str, Any]) -> dict[str, Any]:
    try:
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("Malformed response from OpenRouter") from exc

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise OpenRouterError("OpenRouter response was not valid JSON") from exc


@router.post(
    "/chat",
    response_model=AIChatResponse,
    responses={
        502: {"model": AIChatErrorResponse},
        400: {"model": AIChatErrorResponse},
    },
)
async def ai_chat(
    payload: AIChatRequest,
    client: OpenRouterClient = Depends(get_ai_client),
) -> AIChatResponse:
    messages = _build_messages(payload)

    try:
        raw_response = await client.chat_completion(
            messages,
            temperature=0.2,
            response_format=STRUCTURED_RESPONSE_FORMAT,
        )
        parsed = _parse_response(raw_response)
    except OpenRouterError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    reply_text = parsed.get("assistant_response", "")
    board_update = parsed.get("board_update")

    if board_update is None:
        return AIChatResponse(reply=reply_text, board=None, board_updated=False)

    board_id = board_update.get("id") or payload.board.get("id")
    if not board_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Board update missing board id",
        )

    try:
        saved_board = save_board_state(board_id, board_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AIChatResponse(reply=reply_text, board=saved_board, board_updated=True)
