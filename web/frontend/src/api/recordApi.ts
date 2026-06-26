import { API_BASE, request } from "./apiClient";
import type { ApiResponse } from "../types/game";

const AUTH_TOKEN_KEY = "paoqi_auth_token";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  return token ? { "X-Paoqi-Auth-Token": token } : {};
}

export interface RecordSummary {
  folder_name: string;
  room_code: string;
  winner: string | null;
  end_type: string;
  game_over_reason: string;
  red: { uid: number; username: string; color: string } | null;
  blue: { uid: number; username: string; color: string } | null;
  turn_number: number;
  duration_seconds: number;
  created_at: number;
}

export interface RecordDetail {
  folder_name: string;
  info: {
    room_code: string;
    red: { uid: number; username: string; color: string };
    blue: { uid: number; username: string; color: string };
    winner: string | null;
    end_type: string;
    game_over_reason: string;
    turn_number: number;
    duration_seconds: number;
    created_at: number;
  };
  record_text: string;
  initial_board: BoardCell[][];
  steps: RecordStep[];
  chat: { sender: string; color: string; text: string; time: number }[];
}

export type BoardCell = { color: "R" | "B"; level: number } | null;

export interface RecordStep {
  step: number;
  action_text: string;
  action_type: string;
  actor_color: "R" | "B" | null;
  current_player: string;
  phase: string;
  board: BoardCell[][];
}

export function getUserRecords(
  uid: number,
): Promise<ApiResponse<{ records: RecordSummary[] }>> {
  return request(`/user/${uid}/records`, undefined, authHeaders);
}

export function getRecordDetail(
  folderName: string,
): Promise<ApiResponse<RecordDetail>> {
  return request(
    `/records/${encodeURIComponent(folderName)}`,
    undefined,
    authHeaders,
  );
}

async function downloadAuthenticated(
  path: string,
  fallbackFilename: string,
): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(`下载失败：HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fallbackFilename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function downloadRecord(folderName: string): Promise<void> {
  return downloadAuthenticated(
    `/records/${encodeURIComponent(folderName)}/download`,
    `${folderName}.zip`,
  );
}

export function downloadAllRecords(uid: number): Promise<void> {
  return downloadAuthenticated(
    `/user/${uid}/records/download`,
    "paoqi-records.zip",
  );
}
