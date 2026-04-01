import type { ApiResponse, GameAction, GamePayload } from "../types/game";

const RAW_API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const API_BASE = RAW_API_BASE.replace(/\/+$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...options
  });

  const data = await response.json();
  return data;
}

export async function healthCheck(): Promise<ApiResponse<any>> {
  return request("/health", {
    method: "GET"
  });
}

export async function newGame(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/new-game", {
    method: "POST"
  });
}

export async function getState(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/state", {
    method: "GET"
  });
}

export async function applyAction(action: GameAction): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/apply-action", {
    method: "POST",
    body: JSON.stringify({ action })
  });
}

export async function previewAction(action: GameAction): Promise<ApiResponse<any>> {
  return request<any>("/preview-action", {
    method: "POST",
    body: JSON.stringify({ action })
  });
}

export async function confirmPending(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/confirm-pending", {
    method: "POST"
  });
}

export async function restartGame(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/restart", {
    method: "POST"
  });
}

export async function undoAction(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/undo", {
    method: "POST"
  });
}

export async function endGameByAgreement(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/endgame", {
    method: "POST"
  });
}

export async function resignGame(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/resign", {
    method: "POST"
  });
}

export async function saveToSlot(slot: number): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>(`/save/${slot}`, {
    method: "POST"
  });
}

export async function loadFromSlot(slot: number): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>(`/load/${slot}`, {
    method: "POST"
  });
}

export async function exportRecord(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/export-record", {
    method: "GET"
  });
}

export async function getSaveSlots(): Promise<ApiResponse<any>> {
  return request<any>("/save-slots", {
    method: "GET"
  });
}