import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { authApi, type UserProfile } from "../api/authApi";

const AUTH_TOKEN_KEY = "paoqi_auth_token";

export interface AuthContextValue {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  login: (
    username: string,
    password: string,
  ) => Promise<{ ok: boolean; message: string }>;
  register: (
    username: string,
    password: string,
    confirmPassword: string,
    introLetter: string,
  ) => Promise<{ ok: boolean; message: string }>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth 必须在 AuthProvider 内部使用");
  }
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const res = await authApi.me();
      if (res.ok) {
        setUser(res.data.user);
      } else {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setUser(null);
      }
    } catch {
      // 网络错误，保留 token 让用户下次再试
      setUser(null);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(
    async (username: string, password: string) => {
      const res = await authApi.login(username, password);
      if (res.ok) {
        localStorage.setItem(AUTH_TOKEN_KEY, res.data.token);
        setUser(res.data.user);
      }
      return { ok: res.ok, message: res.message };
    },
    [],
  );

  const register = useCallback(
    async (
      username: string,
      password: string,
      confirmPassword: string,
      introLetter: string,
    ) => {
      const res = await authApi.register(
        username,
        password,
        confirmPassword,
        introLetter,
      );
      if (res.ok) {
        localStorage.setItem(AUTH_TOKEN_KEY, res.data.token);
        setUser(res.data.user);
      }
      return { ok: res.ok, message: res.message };
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // 即使后端调用失败也要清除本地状态
    }
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setUser(null);
  }, []);

  const value: AuthContextValue = {
    user,
    isAuthenticated: user !== null,
    isAuthLoading: isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
