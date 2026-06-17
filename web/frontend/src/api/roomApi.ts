import { request } from "./apiClient";
import type { ApiResponse } from "../types/game";

const AUTH_TOKEN_KEY = "paoqi_auth_token";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (token) return { "X-Paoqi-Auth-Token": token };
  return {};
}

export interface RoomInfo {
  code: string;
  player_count: number;
  game_started: boolean;
  red_username: string;
  created_at: number;
}

export function createRoom(): Promise<ApiResponse<{ room_code: string }>> {
  return request("/rooms", { method: "POST" }, authHeaders);
}

export function listRooms(): Promise<ApiResponse<{ rooms: RoomInfo[] }>> {
  return request("/rooms", { method: "GET" }, authHeaders);
}
