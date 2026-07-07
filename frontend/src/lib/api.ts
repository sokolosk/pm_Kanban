import type { BoardData } from "./kanban";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function apiLogin(username: string, password: string) {
  const response = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return handleResponse<{
    access_token: string;
    user: { id: number; username: string };
  }>(response);
}

export async function apiLogout(token: string) {
  await fetch(`${API_BASE}/api/logout`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function fetchBoards(token: string) {
  const response = await fetch(`${API_BASE}/api/boards/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  return handleResponse<{ boards: any[] }>(response);
}

export async function saveBoard(token: string, boardId: string, boardData: any) {
  const response = await fetch(`${API_BASE}/api/boards/${boardId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(boardData),
  });
  return handleResponse<any>(response);
}

export type AIChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AIChatResponse = {
  reply: string;
  board: BoardData | null;
  board_updated: boolean;
};

export async function aiChat(
  token: string,
  payload: { board: BoardData; message: string; history: AIChatMessage[] }
) {
  const response = await fetch(`${API_BASE}/api/ai/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<AIChatResponse>(response);
}