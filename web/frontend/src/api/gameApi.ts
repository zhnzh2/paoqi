import type { ApiResponse, GameAction, GamePayload } from "../types/game";

const RAW_API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const API_BASE = RAW_API_BASE.replace(/\/+$/, "");
const SESSION_STORAGE_KEY = "paoqi_web_session_id";

function createSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getSessionId(): string {
  const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const sessionId = createSessionId();
  window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  return sessionId;
}

async function request<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const headers = new Headers(options?.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Paoqi-Session-Id", getSessionId());

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    return {
      ok: false,
      message: data?.message ?? `请求失败：HTTP ${response.status}`,
      data: null
    };
  }

  if (!data) {
    return {
      ok: false,
      message: "请求失败：后端返回了非 JSON 响应。",
      data: null
    };
  }

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
