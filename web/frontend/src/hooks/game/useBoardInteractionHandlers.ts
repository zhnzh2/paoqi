import { applyAction, confirmPending } from "../../api/gameApi";
import { findActionByCell } from "../../utils/gameBoardUtils";
import type { GamePayload } from "../../types/game";

type HoveredCell = { x: number; y: number } | null;

type UseBoardInteractionHandlersParams = {
  payload: GamePayload | null;
  isBoardBusy: boolean;
  modalCount: number;
  onRunAction: (
    action: () => Promise<any>,
    scope?: "board" | "sidebar"
  ) => Promise<void>;
  onStatusMessage: (message: string) => void;
  onStatusIsError: (value: boolean) => void;
  onHoveredCellChange: (cell: HoveredCell) => void;
};

export default function useBoardInteractionHandlers({
  payload,
  isBoardBusy,
  modalCount,
  onRunAction,
  onStatusMessage,
  onStatusIsError,
  onHoveredCellChange
}: UseBoardInteractionHandlersParams) {
  async function handleBoardCellClick(x: number, y: number) {
    if (!payload || isBoardBusy || modalCount > 0 || payload.game_over) {
      return;
    }

    if (payload.has_pending_auto_action) {
      onStatusMessage("正在确认自动动作...");
      onStatusIsError(false);
      await onRunAction(confirmPending, "board");
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

    await onRunAction(() => applyAction(action), "board");
    onHoveredCellChange(null);
  }

  function handleBoardCellHover(x: number, y: number) {
    if (isBoardBusy || modalCount > 0 || payload?.game_over) {
      return;
    }
    onHoveredCellChange({ x, y });
  }

  function handleBoardCellLeave() {
    onHoveredCellChange(null);
  }

  return {
    handleBoardCellClick,
    handleBoardCellHover,
    handleBoardCellLeave
  };
}