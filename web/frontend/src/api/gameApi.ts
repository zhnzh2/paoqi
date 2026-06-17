import { request } from "./apiClient";
import type { ApiResponse, GameAction, GamePayload } from "../types/game";

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

function sessionHeaders(): Record<string, string> {
  return { "X-Paoqi-Session-Id": getSessionId() };
}

export async function healthCheck(): Promise<ApiResponse<any>> {
  return request("/health", { method: "GET" }, sessionHeaders);
}

export async function newGame(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/new-game", { method: "POST" }, sessionHeaders);
}

export async function getState(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/state", { method: "GET" }, sessionHeaders);
}

export async function applyAction(
  action: GameAction,
): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>(
    "/apply-action",
    { method: "POST", body: JSON.stringify({ action }) },
    sessionHeaders,
  );
}

export async function previewAction(
  action: GameAction,
): Promise<ApiResponse<any>> {
  return request<any>(
    "/preview-action",
    { method: "POST", body: JSON.stringify({ action }) },
    sessionHeaders,
  );
}

export async function confirmPending(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>(
    "/confirm-pending",
    { method: "POST" },
    sessionHeaders,
  );
}

export async function restartGame(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/restart", { method: "POST" }, sessionHeaders);
}

export async function undoAction(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/undo", { method: "POST" }, sessionHeaders);
}

export async function endGameByAgreement(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/endgame", { method: "POST" }, sessionHeaders);
}

export async function resignGame(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>("/resign", { method: "POST" }, sessionHeaders);
}

export async function saveToSlot(
  slot: number,
): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>(
    `/save/${slot}`,
    { method: "POST" },
    sessionHeaders,
  );
}

export async function loadFromSlot(
  slot: number,
): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>(
    `/load/${slot}`,
    { method: "POST" },
    sessionHeaders,
  );
}

export async function exportRecord(): Promise<ApiResponse<GamePayload>> {
  return request<GamePayload>(
    "/export-record",
    { method: "GET" },
    sessionHeaders,
  );
}

export async function getSaveSlots(): Promise<ApiResponse<any>> {
  return request<any>("/save-slots", { method: "GET" }, sessionHeaders);
}
