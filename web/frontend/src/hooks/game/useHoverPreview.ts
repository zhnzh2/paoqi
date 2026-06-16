import { useMemo } from "react";
import { useEngine } from "../../engine/EngineContext";
import { findActionByCell } from "../../utils/gameBoardUtils";
import type { GamePayload } from "../../types/game";

type HoveredCell = { x: number; y: number } | null;
type BoardCell = { color: "R" | "B"; level: number } | null;

type UseHoverPreviewParams = {
  payload: GamePayload | null;
  hoveredCell: HoveredCell;
  busyScope: "none" | "board" | "sidebar";
  modalCount: number;
  showHoverPreview: boolean;
};

export default function useHoverPreview({
  payload,
  hoveredCell,
  busyScope,
  modalCount,
  showHoverPreview
}: UseHoverPreviewParams) {
  const { engine, isReady } = useEngine();

  /**
   * 使用本地引擎同步计算预览棋盘。
   * engine.previewAction() 是同步调用（<1ms），直接用 useMemo。
   * 只有当引擎未就绪时才返回 null（由 GamePage 的 loading 状态兜底）。
   */
  const previewBoardData: BoardCell[][] | null = useMemo(() => {
    // 基础条件检查
    if (!showHoverPreview) {
      return null;
    }

    if (!payload || !hoveredCell) {
      return null;
    }

    if (busyScope !== "none" || modalCount > 0 || payload.game_over || payload.has_pending_auto_action) {
      return null;
    }

    if (!isReady || !engine) {
      return null;
    }

    const action = findActionByCell(
      payload.legal_actions,
      payload.phase,
      hoveredCell.x,
      hoveredCell.y
    );

    if (!action) {
      return null;
    }

    const shouldPreview =
      payload.phase === "drop" ||
      payload.phase === "eat" ||
      payload.phase === "fire" ||
      payload.phase === "muzzle";

    if (!shouldPreview) {
      return null;
    }

    // 本地同步计算预览 —— 无网络延迟！
    const res = engine.previewAction(action);
    if (res.ok && res.preview_snapshot && res.preview_snapshot.board) {
      return res.preview_snapshot.board;
    }

    return null;
  }, [payload, hoveredCell, busyScope, modalCount, showHoverPreview, engine, isReady]);

  return {
    previewBoardData,
    // 保留 setPreviewBoardData 以便接口兼容（本地引擎不再需要外部设置）
    setPreviewBoardData: (_: BoardCell[][] | null) => {},
  };
}
