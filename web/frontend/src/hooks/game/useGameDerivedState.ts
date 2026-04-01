import { useMemo } from "react";
import {
  buildArrowCells,
  buildEmptyBoard,
  buildHighlightedCells,
  buildHoveredCannonCells,
  buildHoveredDropHighlight
} from "../../utils/gameBoardUtils";
import type { GamePayload } from "../../types/game";

type HoveredCell = { x: number; y: number } | null;

type UseGameDerivedStateParams = {
  payload: GamePayload | null;
  hoveredCell: HoveredCell;
  recordPage: number;
  recordPageSize: number;
  showDropHighlight: boolean;
  showEatHighlight: boolean;
  showMuzzleHighlight: boolean;
  showFireHighlight: boolean;
  showArrowHints: boolean;
  showCannonHoverEnhance: boolean;
};

export default function useGameDerivedState({
  payload,
  hoveredCell,
  recordPage,
  recordPageSize,
  showDropHighlight,
  showEatHighlight,
  showMuzzleHighlight,
  showFireHighlight,
  showArrowHints,
  showCannonHoverEnhance
}: UseGameDerivedStateParams) {
  const totalRecordPages = useMemo(() => {
    const total = payload?.history.length ?? 0;
    return Math.max(1, Math.ceil(total / recordPageSize));
  }, [payload, recordPageSize]);

  const pagedHistory = useMemo(() => {
    const history = payload?.history ?? [];
    const start = (recordPage - 1) * recordPageSize;
    return history.slice(start, start + recordPageSize);
  }, [payload, recordPage, recordPageSize]);

  const boardData = useMemo(() => {
    if (!payload?.snapshot?.board) {
      return buildEmptyBoard();
    }
    return payload.snapshot.board;
  }, [payload]);

  const highlightedCells = useMemo(() => {
    const base = buildHighlightedCells(payload, {
      showEatHighlight,
      showMuzzleHighlight,
      showFireHighlight
    });

    const dropHover = buildHoveredDropHighlight(
      payload,
      hoveredCell,
      showDropHighlight
    );

    return {
      ...base,
      ...dropHover
    };
  }, [
    payload,
    hoveredCell,
    showDropHighlight,
    showEatHighlight,
    showMuzzleHighlight,
    showFireHighlight
  ]);

  const hoveredCellKey = useMemo(() => {
    if (!hoveredCell) {
      return null;
    }
    return `${hoveredCell.x},${hoveredCell.y}`;
  }, [hoveredCell]);

  const hoveredCannonCells = useMemo(() => {
    if (!showCannonHoverEnhance) {
      return {};
    }
    return buildHoveredCannonCells(payload, hoveredCell);
  }, [payload, hoveredCell, showCannonHoverEnhance]);

  const arrowCells = useMemo(() => {
    if (!showArrowHints) {
      return {};
    }
    return buildArrowCells(payload);
  }, [payload, showArrowHints]);

  const pendingAutoMessage = useMemo(() => {
    if (!payload) {
      return "";
    }

    if (!payload.has_pending_auto_action) {
      return "";
    }

    if (Array.isArray(payload.auto_action_messages) && payload.auto_action_messages.length > 0) {
      return payload.auto_action_messages[payload.auto_action_messages.length - 1];
    }

    return "当前存在待确认自动动作，请点击“确认自动动作”。";
  }, [payload]);

  return {
    totalRecordPages,
    pagedHistory,
    boardData,
    highlightedCells,
    hoveredCellKey,
    hoveredCannonCells,
    arrowCells,
    pendingAutoMessage
  };
}