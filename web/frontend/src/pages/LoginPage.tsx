import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { isAuthenticated, isAuthLoading, login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // 已登录则跳转到首页
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // 正在验证 token 时显示加载
  if (isAuthLoading) {
    return (
      <div className="auth-page">
        <div className="auth-loading">加载中...</div>
      </div>
    );
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (!username.trim()) {
      setError("请输入用户名");
      return;
    }
    if (!password) {
      setError("请输入密码");
      return;
    }

    setSubmitting(true);
    try {
      const result = await login(username.trim(), password);
      if (result.ok) {
        navigate("/", { replace: true });
      } else {
        setError(result.message);
      }
    } catch {
      setError("网络错误，请检查后端是否在运行。");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">炮棋</h1>
        <p className="auth-subtitle">登录你的账号</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label className="auth-label" htmlFor="login-username">
              用户名
            </label>
            <input
              id="login-username"
              className="auth-input"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={submitting}
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="login-password">
              密码
            </label>
            <input
              id="login-password"
              className="auth-input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
            />
          </div>

          {error ? <div className="auth-error">{error}</div> : null}

          <button
            type="submit"
            className="auth-button"
            disabled={submitting}
          >
            {submitting ? "登录中..." : "登录"}
          </button>
        </form>

        <div className="auth-link-row">
          还没有账号？{" "}
          <Link to="/register" className="auth-link">
            立即注册
          </Link>
        </div>
      </div>
    </div>
  );
}
