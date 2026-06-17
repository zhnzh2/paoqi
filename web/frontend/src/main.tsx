import React, { Component } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

/**
 * 全局错误边界 —— 捕获渲染树中任何未处理的异常，
 * 防止整页白屏/黑屏，至少让用户看到错误信息。
 */
class ErrorBoundary extends Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("炮棋渲染错误：", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            color: "#f88",
            fontFamily: "sans-serif",
            background: "#1a1a1a",
            padding: "2rem",
            boxSizing: "border-box",
          }}
        >
          <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>
            渲染错误
          </div>
          <div
            style={{
              fontSize: "0.85rem",
              color: "#ccc",
              maxWidth: "600px",
              textAlign: "center",
              marginBottom: "1.5rem",
              wordBreak: "break-all",
              lineHeight: 1.6,
            }}
          >
            {this.state.error?.message || "未知错误"}
          </div>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{
              padding: "0.6rem 1.5rem",
              background: "#c74444",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.9rem",
            }}
          >
            重新加载
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
