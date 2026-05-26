import Board from "./Board";
import DangerActionsPanel from "../panels/DangerActionsPanel";

type BoardCell = { color: "R" | "B"; level: number } | null;
type HighlightType = "drop" | "eat" | "muzzle" | "fire" | null;

type GameBoardSectionProps = {
  boardData: BoardCell[][];
  previewBoardData: BoardCell[][];
  highlightedCells: Record<string, HighlightType>;
  hoveredCellKey: string | null;
  hoveredCannonCells: Record<string, true>;
  arrowCells: Record<string, string>;
  activePlayer: "R" | "B" | null;
  showCoordText: boolean;
  isBusy: boolean;
  dangerDisabled: boolean;
  onCellClick: (x: number, y: number) => void | Promise<void>;
  onCellHover: (x: number, y: number) => void;
  onCellLeave: () => void;
  onEndgame: () => void;
  onResign: () => void;
  onBackToMenu: () => void;
};

export default function GameBoardSection({
  boardData,
  previewBoardData,
  highlightedCells,
  hoveredCellKey,
  hoveredCannonCells,
  arrowCells,
  activePlayer,
  showCoordText,
  isBusy,
  dangerDisabled,
  onCellClick,
  onCellHover,
  onCellLeave,
  onEndgame,
  onResign,
  onBackToMenu
}: GameBoardSectionProps) {
  return (
    <div className="left-column">
      <h1>炮棋 Web 原型</h1>

      <Board
        boardData={boardData}
        previewBoardData={previewBoardData}
        highlightedCells={highlightedCells}
        hoveredCellKey={hoveredCellKey}
        hoveredCannonCells={hoveredCannonCells}
        arrowCells={arrowCells}
        activePlayer={activePlayer}
        showCoordText={showCoordText}
        isBusy={isBusy}
        onCellClick={onCellClick}
        onCellHover={onCellHover}
        onCellLeave={onCellLeave}
      />

      <DangerActionsPanel
        disabled={dangerDisabled}
        onEndgame={onEndgame}
        onResign={onResign}
        onBackToMenu={onBackToMenu}
      />
    </div>
  );
}