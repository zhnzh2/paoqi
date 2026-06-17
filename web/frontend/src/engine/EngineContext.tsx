/**
 * 引擎 React Context —— 在组件树中提供 PaoqiEngine 实例。
 *
 * 加载流程：
 *   1. 检查 IndexedDB 缓存版本 → 不匹配则清理
 *   2. 连接 jsDelivr CDN → 下载 Pyodide 运行时
 *   3. 初始化 Python 环境 → 写入 core/ 模块 → 编译引擎
 *   4. 就绪
 *
 * 失败处理：
 *   - 缓存损坏 → 自动清理后重试一次
 *   - CDN 不通 → 显示错误 + 手动重试按钮
 */

import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { PaoqiEngine } from "./pyodideEngine";
import type { EngineProgress } from "./pyodideEngine";

export interface EngineContextValue {
  engine: PaoqiEngine | null;
  isReady: boolean;
  isLoading: boolean;
  progress: EngineProgress;
  errorMessage: string | null;
  /** 手动重试（清缓存后重新初始化） */
  retry: () => void;
}

const EngineContext = createContext<EngineContextValue>({
  engine: null,
  isReady: false,
  isLoading: true,
  progress: { stage: "正在初始化...", percent: 0 },
  errorMessage: null,
  retry: () => {},
});

export function useEngine(): EngineContextValue {
  return useContext(EngineContext);
}

// 进度条样式（内联以保证不依赖 CSS 加载）
const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    color: "#ccc",
    fontFamily: "sans-serif",
    background: "#1a1a1a",
    padding: "2rem",
    boxSizing: "border-box" as const,
  },
  title: {
    fontSize: "1.4rem",
    marginBottom: "0.3rem",
    color: "#eee",
  },
  subtitle: {
    fontSize: "0.85rem",
    color: "#999",
    marginBottom: "1.2rem",
  },
  barOuter: {
    width: "320px",
    maxWidth: "90vw",
    height: "8px",
    background: "#333",
    borderRadius: "4px",
    overflow: "hidden" as const,
    marginBottom: "0.6rem",
  },
  barInner: (pct: number) => ({
    height: "100%",
    width: `${Math.min(100, Math.max(0, pct))}%`,
    background: pct >= 100 ? "#4caf50" : "#c74444",
    borderRadius: "4px",
    transition: "width 0.4s ease",
  }),
  percent: {
    fontSize: "0.8rem",
    color: "#888",
    marginBottom: "1.5rem",
  },
  stage: {
    fontSize: "0.85rem",
    color: "#aaa",
  },
  errorBox: {
    maxWidth: "500px",
    textAlign: "center" as const,
    lineHeight: 1.7,
    marginBottom: "1.5rem",
    color: "#f88",
    fontSize: "0.85rem",
    whiteSpace: "pre-wrap" as const,
    wordBreak: "break-word" as const,
  },
  retryBtn: {
    padding: "0.6rem 1.5rem",
    background: "#c74444",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "0.9rem",
  },
};

export function EngineProvider({ children }: { children: React.ReactNode }) {
  const [engine, setEngine] = useState<PaoqiEngine | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [progress, setProgress] = useState<EngineProgress>({
    stage: "正在初始化...",
    percent: 0,
  });
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const retryCountRef = useRef(0);

  const boot = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    setProgress({ stage: "正在检查缓存...", percent: 0 });

    try {
      const eng = await PaoqiEngine.create((p) => {
        setProgress({ ...p });
      });

      setEngine(eng);
      setIsLoading(false);
      setProgress({ stage: "引擎就绪", percent: 100 });
    } catch (err) {
      setErrorMessage(String(err));
      setIsLoading(false);
    }
  };

  useEffect(() => {
    boot();
  }, []);

  const retry = () => {
    retryCountRef.current += 1;

    // 清理所有可能损坏的缓存和旧数据
    try { indexedDB.deleteDatabase("/pyodide"); } catch { /* 忽略 */ }
    localStorage.removeItem("paoqi_engine_version");
    localStorage.removeItem("paoqi_current_game");
    for (let i = 1; i <= 3; i++) {
      localStorage.removeItem(`paoqi_save_slot_${i}`);
    }

    boot();
  };

  const value: EngineContextValue = {
    engine,
    isReady: engine !== null && !isLoading,
    isLoading,
    progress,
    errorMessage,
    retry,
  };

  return (
    <EngineContext.Provider value={value}>
      {children}
    </EngineContext.Provider>
  );
}

/**
 * 引擎加载界面 —— 在 App 层渲染，作为 children 之前展示。
 * 仅在加载中或出错时显示。
 */
export function EngineLoadingScreen() {
  const { isLoading, progress, errorMessage, retry } = useEngine();

  if (!isLoading && !errorMessage) {
    return null;
  }

  return (
    <div style={styles.container}>
      <div style={styles.title}>♟️ 炮棋</div>

      {errorMessage ? (
        <>
          <div style={styles.subtitle}>引擎加载失败</div>
          <div style={styles.errorBox}>{errorMessage}</div>
          <button style={styles.retryBtn} onClick={retry}>
            清理缓存并重试
          </button>
        </>
      ) : (
        <>
          <div style={styles.subtitle}>正在部署引擎...</div>

          {/* 进度条 */}
          <div style={styles.barOuter}>
            <div style={styles.barInner(progress.percent)} />
          </div>

          {/* 百分比数字 */}
          <div style={styles.percent}>{progress.percent}%</div>

          {/* 当前阶段 */}
          <div style={styles.stage}>{progress.stage}</div>
        </>
      )}
    </div>
  );
}
