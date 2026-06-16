/**
 * 引擎 React Context —— 在组件树中提供 PaoqiEngine 实例。
 * 引擎初始化在 App 层完成，通过 Context 向下传递。
 */

import React, { createContext, useContext, useEffect, useState } from "react";
import { PaoqiEngine } from "./pyodideEngine";
import type { EngineProgressCallback } from "./pyodideEngine";

export interface EngineContextValue {
  engine: PaoqiEngine | null;
  isReady: boolean;
  isLoading: boolean;
  progressMessage: string;
  errorMessage: string | null;
}

const EngineContext = createContext<EngineContextValue>({
  engine: null,
  isReady: false,
  isLoading: true,
  progressMessage: "正在初始化引擎...",
  errorMessage: null,
});

export function useEngine(): EngineContextValue {
  return useContext(EngineContext);
}

/**
 * 引擎 Provider。负责：
 * 1. 在挂载时初始化 Pyodide 引擎（单例）
 * 2. 将引擎实例通过 Context 提供
 * 3. 展示加载进度
 */
export function EngineProvider({ children }: { children: React.ReactNode }) {
  const [engine, setEngine] = useState<PaoqiEngine | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [progressMessage, setProgressMessage] = useState("正在初始化引擎...");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        const onProgress: EngineProgressCallback = (msg) => {
          if (!cancelled) {
            setProgressMessage(msg);
          }
        };

        const eng = await PaoqiEngine.create(onProgress);

        if (!cancelled) {
          setEngine(eng);
          setIsLoading(false);
          setProgressMessage("引擎就绪。");
        }
      } catch (err) {
        if (!cancelled) {
          setErrorMessage(String(err));
          setIsLoading(false);
        }
      }
    }

    boot();

    return () => {
      cancelled = true;
    };
  }, []);

  const value: EngineContextValue = {
    engine,
    isReady: engine !== null && !isLoading,
    isLoading,
    progressMessage,
    errorMessage,
  };

  return (
    <EngineContext.Provider value={value}>
      {children}
    </EngineContext.Provider>
  );
}
