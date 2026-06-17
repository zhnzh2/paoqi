import { useEffect, useRef, useState, useCallback } from "react";

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_DELAY_MS = 2000;

export type ConnectionState =
  | "connecting"
  | "connected"
  | "disconnected"
  | "error";

type UseRoomWebSocketParams = {
  roomCode: string;
  onMessage: (data: any) => void;
  onDisconnect: () => void;
};

type UseRoomWebSocketReturn = {
  send: (data: any) => void;
  isConnected: boolean;
  connectionState: ConnectionState;
  error: string | null;
};

/**
 * 从 VITE_API_BASE_URL 推导 WebSocket 地址。
 * http://127.0.0.1:8000/api → ws://127.0.0.1:8000
 */
function deriveWsBase(): string {
  const raw =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
  return raw
    .replace(/^http/, "ws")
    .replace(/\/api\/?$/, "");
}

export default function useRoomWebSocket({
  roomCode,
  onMessage,
  onDisconnect,
}: UseRoomWebSocketParams): UseRoomWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("connecting");
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // 保存回调引用以避免闭包过期
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;
  const onDisconnectRef = useRef(onDisconnect);
  onDisconnectRef.current = onDisconnect;

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const token = localStorage.getItem("paoqi_auth_token");
    if (!token) {
      setError("未登录");
      setConnectionState("error");
      return;
    }

    const wsBase = deriveWsBase();
    const url = `${wsBase}/ws/room/${roomCode}?token=${encodeURIComponent(token)}`;

    setConnectionState("connecting");
    setError(null);

    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      setError("无法创建 WebSocket 连接");
      setConnectionState("error");
      return;
    }

    wsRef.current = socket;

    socket.onopen = () => {
      if (!mountedRef.current) return;
      setIsConnected(true);
      setConnectionState("connected");
      setError(null);
      reconnectCountRef.current = 0;
    };

    socket.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current(data);
      } catch {
        // 忽略无法解析的消息
      }
    };

    socket.onclose = (event) => {
      if (!mountedRef.current) return;
      setIsConnected(false);
      setConnectionState("disconnected");
      onDisconnectRef.current();

      // 非正常关闭时尝试重连
      if (event.code !== 1000 && reconnectCountRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectCountRef.current);
        reconnectCountRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, delay);
      } else if (reconnectCountRef.current >= MAX_RECONNECT_ATTEMPTS) {
        setError("连接失败，已达到最大重试次数");
        setConnectionState("error");
      }
    };

    socket.onerror = () => {
      // onclose 会随后触发，在那里处理重连
    };
  }, [roomCode]);

  // 发送消息
  const send = useCallback((data: any) => {
    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    }
  }, []);

  // 挂载时连接，卸载时清理
  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      const socket = wsRef.current;
      if (socket) {
        socket.onclose = null; // 阻止重连
        socket.close(1000, "组件卸载");
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { send, isConnected, connectionState, error };
}
