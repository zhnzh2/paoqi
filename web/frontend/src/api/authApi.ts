import { request } from "./apiClient";
import type { ApiResponse } from "../types/game";

const AUTH_TOKEN_KEY = "paoqi_auth_token";

export type UserRole = "站主" | "管理员" | "用户";

export interface UserProfile {
  uid: number;
  username: string;
  role: UserRole;
  intro_letter: string;
  registered_at: string;
}

interface AuthPayload {
  token: string;
  user: UserProfile;
}

function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (token) {
    return { "X-Paoqi-Auth-Token": token };
  }
  return {};
}

export const authApi = {
  async login(
    username: string,
    password: string,
  ): Promise<ApiResponse<AuthPayload>> {
    return request<AuthPayload>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ username, password }),
      },
      authHeaders,
    );
  },

  async register(
    username: string,
    password: string,
    confirmPassword: string,
    introLetter: string,
  ): Promise<ApiResponse<AuthPayload>> {
    return request<AuthPayload>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify({
          username,
          password,
          confirm_password: confirmPassword,
          intro_letter: introLetter,
        }),
      },
      authHeaders,
    );
  },

  async me(): Promise<ApiResponse<{ user: UserProfile }>> {
    return request<{ user: UserProfile }>(
      "/auth/me",
      { method: "GET" },
      authHeaders,
    );
  },

  async logout(): Promise<ApiResponse<null>> {
    return request<null>(
      "/auth/logout",
      { method: "POST" },
      authHeaders,
    );
  },

  // --- 用户 Profile ---

  async getUserProfile(
    uid: number,
  ): Promise<ApiResponse<{ user: UserProfile }>> {
    return request<{ user: UserProfile }>(
      `/user/${uid}`,
      { method: "GET" },
      authHeaders,
    );
  },

  async updateProfile(
    introLetter: string,
  ): Promise<ApiResponse<{ user: UserProfile }>> {
    return request<{ user: UserProfile }>(
      "/user/update-profile",
      {
        method: "POST",
        body: JSON.stringify({ intro_letter: introLetter }),
      },
      authHeaders,
    );
  },

  async changePassword(
    oldPassword: string,
    newPassword: string,
  ): Promise<ApiResponse<null>> {
    return request<null>(
      "/user/change-password",
      {
        method: "POST",
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        }),
      },
      authHeaders,
    );
  },

  // --- 用户设置 ---

  async getSettings(): Promise<ApiResponse<{ settings: Record<string, boolean> }>> {
    return request<{ settings: Record<string, boolean> }>(
      "/user/settings",
      { method: "GET" },
      authHeaders,
    );
  },

  async saveSettings(
    settings: Record<string, boolean>,
  ): Promise<ApiResponse<null>> {
    return request<null>(
      "/user/settings",
      {
        method: "PUT",
        body: JSON.stringify({ settings }),
      },
      authHeaders,
    );
  },
};
