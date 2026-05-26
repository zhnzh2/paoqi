import { useEffect, useRef, useState } from "react";
import { previewAction } from "../../api/gameApi";
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
  const [previewBoardData, setPreviewBoardData] = useState<BoardCell[][] | null>(null);
  const previewRequestIdRef = useRef(0);

  useEffect(() => {
    if (payload?.game_over) {
      setPreviewBoardData(null);
    }
  }, [payload?.game_over]);

  useEffect(() => {
    async function runPreview() {
      if (!showHoverPreview) {
        setPreviewBoardData(null);
        return;
      }

      if (!payload || !hoveredCell) {
        setPreviewBoardData(null);
        return;
      }

      if (busyScope !== "none" || modalCount > 0 || payload.game_over || payload.has_pending_auto_action) {
        setPreviewBoardData(null);
        return;
      }

      const action = findActionByCell(
        payload.legal_actions,
        payload.phase,
        hoveredCell.x,
        hoveredCell.y
      );

      if (!action) {
        setPreviewBoardData(null);
        return;
      }

      const shouldPreview =
        payload.phase === "drop" ||
        payload.phase === "eat" ||
        payload.phase === "fire" ||
        payload.phase === "muzzle";

      if (!shouldPreview) {
        setPreviewBoardData(null);
        return;
      }

      const requestId = ++previewRequestIdRef.current;

      try {
        const res = await previewAction(action);

        if (requestId !== previewRequestIdRef.current) {
          return;
        }

        if (res.ok && res.preview_snapshot && res.preview_snapshot.board) {
          setPreviewBoardData(res.preview_snapshot.board);
        } else {
          setPreviewBoardData(null);
        }
      } catch {
        if (requestId === previewRequestIdRef.current) {
          setPreviewBoardData(null);
        }
      }
    }

    runPreview();
  }, [payload, hoveredCell, busyScope, modalCount, showHoverPreview]);

  return {
    previewBoardData,
    setPreviewBoardData
  };
}