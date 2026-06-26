import type { ApiResponse } from "../types/game";

const RAW_API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

export const API_BASE = RAW_API_BASE.replace(/\/+$/, "");

/**
 * 通用 API 请求函数。
 *
 * @param path       - API 路径（相对于 API_BASE，如 "/health"）
 * @param options    - fetch 选项
 * @param extraHeaders - 额外的请求头注入函数
 * @returns ApiResponse<T>
 */
export async function request<T>(
  path: string,
  options?: RequestInit,
  extraHeaders?: () => Record<string, string>,
): Promise<ApiResponse<T>> {
  const headers = new Headers(options?.headers);
  headers.set("Content-Type", "application/json");

  if (extraHeaders) {
    const extra = extraHeaders();
    for (const [key, value] of Object.entries(extra)) {
      headers.set(key, value);
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    return {
      ok: false,
      message:
        data?.message ??
        data?.detail ??
        `请求失败：HTTP ${response.status}`,
      data: null,
    };
  }

  if (!data) {
    return {
      ok: false,
      message: "请求失败：后端返回了非 JSON 响应。",
      data: null,
    };
  }

  return data;
}
