from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import Any

from database import (
    authenticate_user,
    get_board,
    get_user,
    get_user_boards,
    save_board_state,
    create_board,
    create_session,
    delete_session,
    get_user_by_token,
)

router = APIRouter(prefix="/api", tags=["kanban"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    token = credentials.credentials
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/login")
async def login(payload: LoginRequest):
    """Authenticate user and return session token"""
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_session(user["id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "username": user["username"]},
    }

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    delete_session(token)
    return {"detail": "Logged out"}

@router.get("/boards/me")
async def get_my_boards(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    boards = get_user_boards(user_id)

    if not boards:
        board = create_board(user_id, "My Kanban Board")
        boards = [board]

    return {"boards": boards}

@router.get("/boards/{board_id}")
async def get_board_endpoint(
    board_id: str,
    current_user: dict = Depends(get_current_user)
):
    board = get_board(board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if board["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this board",
        )

    return board

@router.put("/boards/{board_id}")
async def update_board_endpoint(
    board_id: str,
    board_data: dict,
    current_user: dict = Depends(get_current_user)
):
    existing_board = get_board(board_id)
    if not existing_board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if existing_board["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this board",
        )

    updated_board = save_board_state(board_id, board_data)
    return updated_board

@router.post("/boards")
async def create_board_endpoint(
    board_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new board for the current user"""
    title = board_data.get("title", "New Board")
    board = create_board(current_user["id"], title)
    return board