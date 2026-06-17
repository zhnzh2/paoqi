import { useEffect } from "react";
import { useEngine } from "../../engine/EngineContext";
import type { GamePayload } from "../../types/game";

type UseGameLifecycleParams = {
  openLoadModalOnMount: boolean;
  payload: GamePayload | null;
  recordPage: number;
  totalRecordPages: number;
  onOpenModal: (name: string) => void;
  onHoveredCellClear: () => void;
  onPayloadChange: (payload: GamePayload) => void;
  onStatusMessage: (message: string) => void;
  onStatusIsError: (value: boolean) => void;
  onRecordPageChange: (value: number) => void;
};

/**
 * 游戏生命周期 Hook —— 使用本地引擎替代 HTTP API 调用。
 * 引擎就绪后直接本地创建/恢复对局。
 */
export default function useGameLifecycle({
  openLoadModalOnMount,
  payload,
  recordPage,
  totalRecordPages,
  onOpenModal,
  onHoveredCellClear,
  onPayloadChange,
  onStatusMessage,
  onStatusIsError,
  onRecordPageChange
}: UseGameLifecycleParams) {
  const { engine, isReady } = useEngine();

  // 挂载时：如果指定了打开读档弹窗，则打开
  useEffect(() => {
    if (openLoadModalOnMount) {
      onOpenModal("save-load");
    }
  }, [openLoadModalOnMount, onOpenModal]);

  // 游戏结束时清除悬停
  useEffect(() => {
    if (payload?.game_over) {
      onHoveredCellClear();
    }
  }, [payload?.game_over, onHoveredCellClear]);

  // 引擎就绪后初始化对局（仅在首次挂载且 payload 为空时）
  useEffect(() => {
    if (!isReady || !engine || payload) {
      return;
    }

    try {
      // 尝试恢复之前未完成的本地对局
      const saved = localStorage.getItem("paoqi_current_game");
      if (saved) {
        try {
          const data = JSON.parse(saved);
          if ((data.history?.length ?? 0) > 0) {
            const p = engine.importState(data);
            onPayloadChange(p);
            onStatusMessage("已恢复上次对局。");
            onStatusIsError(false);
            return;
          }
        } catch (parseErr) {
          // JSON 损坏或引擎 importState 失败——清除损坏数据，重新开始
          console.warn("恢复对局失败，将创建新对局：", parseErr);
          localStorage.removeItem("paoqi_current_game");
        }
      }

      // 创建全新对局
      const p = engine.newGame();
      onPayloadChange(p);
      onStatusMessage("引擎就绪，对局已开始。");
      onStatusIsError(false);
    } catch (engineErr) {
      // 引擎调用异常——显示错误但不触发 ErrorBoundary
      console.error("引擎初始化对局失败：", engineErr);
      onStatusMessage(`引擎错误：${String(engineErr)}`);
      onStatusIsError(true);
    }
  }, [isReady, engine, payload, onPayloadChange, onStatusMessage, onStatusIsError]);

  // 棋谱翻页越界修正
  useEffect(() => {
    if (recordPage > totalRecordPages) {
      onRecordPageChange(totalRecordPages);
    }
  }, [recordPage, totalRecordPages, onRecordPageChange]);
}
