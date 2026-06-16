import { useCallback } from "react";
import { useEngine } from "../../engine/EngineContext";
import { findActionByCell } from "../../utils/gameBoardUtils";
import type { GamePayload } from "../../types/game";

type HoveredCell = { x: number; y: number } | null;

type UseBoardInteractionHandlersParams = {
  payload: GamePayload | null;
  isBoardBusy: boolean;
  modalCount: number;
  onStatusMessage: (message: string) => void;
  onStatusIsError: (value: boolean) => void;
  onHoveredCellChange: (cell: HoveredCell) => void;
  onPayloadChange: (payload: GamePayload) => void;
};

export default function useBoardInteractionHandlers({
  payload,
  isBoardBusy,
  modalCount,
  onStatusMessage,
  onStatusIsError,
  onHoveredCellChange,
  onPayloadChange
}: UseBoardInteractionHandlersParams) {
  const { engine, isReady } = useEngine();

  const handleBoardCellClick = useCallback(
    async (x: number, y: number) => {
      if (!payload || isBoardBusy || modalCount > 0 || payload.game_over) {
        return;
      }

      if (!isReady || !engine) {
        onStatusMessage("引擎尚未就绪，请稍后重试。");
        onStatusIsError(true);
        return;
      }

      // 处理待确认自动动作
      if (payload.has_pending_auto_action) {
        onStatusMessage("正在确认自动动作...");
        onStatusIsError(false);
        const result = engine.confirmPending();
        if (result.ok && result.payload) {
          onPayloadChange(result.payload);
          onStatusMessage(result.message);
        } else {
          onStatusMessage(result.message);
          onStatusIsError(true);
        }
        onHoveredCellChange(null);
        return;
      }

      const action = findActionByCell(payload.legal_actions, payload.phase, x, y);
      if (!action) {
        onStatusMessage(`(${x}, ${y}) 不是当前阶段可执行的位置，或该位置对应多个候选动作。`);
        onStatusIsError(true);
        return;
      }

      onStatusMessage(`正在处理 (${x}, ${y}) 的点击...`);
      onStatusIsError(false);

      // 本地引擎同步执行 —— 无网络延迟！
      const result = engine.applyAction(action);
      if (result.ok && result.payload) {
        onPayloadChange(result.payload);
        onStatusMessage(result.message);
      } else {
        onStatusMessage(result.message);
        onStatusIsError(true);
      }
      onHoveredCellChange(null);
    },
    [payload, isBoardBusy, modalCount, engine, isReady, onPayloadChange, onStatusMessage, onStatusIsError, onHoveredCellChange]
  );

  const handleBoardCellHover = useCallback(
    (x: number, y: number) => {
      if (isBoardBusy || modalCount > 0 || payload?.game_over) {
        return;
      }
      onHoveredCellChange({ x, y });
    },
    [isBoardBusy, modalCount, payload?.game_over, onHoveredCellChange]
  );

  const handleBoardCellLeave = useCallback(() => {
    onHoveredCellChange(null);
  }, [onHoveredCellChange]);

  return {
    handleBoardCellClick,
    handleBoardCellHover,
    handleBoardCellLeave
  };
}
