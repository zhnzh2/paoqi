import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function RegisterPage() {
  const { isAuthenticated, isAuthLoading, register } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [introLetter, setIntroLetter] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // 已登录则跳转到首页
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

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
    if (username.trim().length < 2) {
      setError("用户名至少需要 2 个字符");
      return;
    }
    if (!password) {
      setError("请输入密码");
      return;
    }
    if (password !== confirmPassword) {
      setError("两次输入的密码不一致");
      return;
    }
    if (!introLetter.trim()) {
      setError("请填写介绍信");
      return;
    }

    setSubmitting(true);
    try {
      const result = await register(
        username.trim(),
        password,
        confirmPassword,
        introLetter.trim(),
      );
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
        <p className="auth-subtitle">创建新账号</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label className="auth-label" htmlFor="reg-username">
              用户名
            </label>
            <input
              id="reg-username"
              className="auth-input"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={submitting}
              maxLength={32}
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="reg-password">
              密码
            </label>
            <input
              id="reg-password"
              className="auth-input"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              maxLength={128}
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="reg-confirm-password">
              确认密码
            </label>
            <input
              id="reg-confirm-password"
              className="auth-input"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={submitting}
              maxLength={128}
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="reg-intro-letter">
              介绍信
            </label>
            <textarea
              id="reg-intro-letter"
              className="auth-textarea"
              value={introLetter}
              onChange={(e) => setIntroLetter(e.target.value)}
              disabled={submitting}
              maxLength={500}
              rows={4}
              placeholder="请简单介绍一下自己..."
            />
          </div>

          {error ? <div className="auth-error">{error}</div> : null}

          <button
            type="submit"
            className="auth-button"
            disabled={submitting}
          >
            {submitting ? "注册中..." : "注册"}
          </button>
        </form>

        <div className="auth-link-row">
          已有账号？{" "}
          <Link to="/login" className="auth-link">
            去登录
          </Link>
        </div>
      </div>
    </div>
  );
}
