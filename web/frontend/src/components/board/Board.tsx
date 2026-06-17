import Cell from "./Cell";

type PieceData = {
  color: "R" | "B";
  level: number;
} | null;

type HighlightType = "drop" | "eat" | "muzzle" | "fire" | null;

type BoardProps = {
  boardData: PieceData[][];
  previewBoardData: PieceData[][] | null;
  highlightedCells: Record<string, HighlightType>;
  hoveredCellKey: string | null;
  hoveredCannonCells: Record<string, true>;
  arrowCells: Record<string, string>;
  activePlayer: "R" | "B" | null;
  showCoordText: boolean;
  isBusy: boolean;
  onCellClick: (x: number, y: number) => void | Promise<void>;
  onCellHover: (x: number, y: number) => void;
  onCellLeave: () => void;
};

function makeCoordText(x: number, y: number): string {
  return `${x},${y}`;
}

function makeCellKey(x: number, y: number): string {
  return `${x},${y}`;
}

function piecesEqual(a: PieceData, b: PieceData): boolean {
  if (a == null || b == null) {
    return a == b;
  }

  return a.color === b.color && a.level === b.level;
}

export default function Board({
  boardData,
  previewBoardData,
  highlightedCells,
  hoveredCellKey,
  hoveredCannonCells,
  arrowCells,
  activePlayer,
  showCoordText,
  isBusy,
  onCellClick,
  onCellHover,
  onCellLeave
}: BoardProps) {
  const previewActive = previewBoardData !== null;

  return (
    <div className={`board-panel ${isBusy ? "board-panel-busy" : ""}`}>
      <div className="board-shell">
        <div className="board-top-coords">
          <div className="board-corner" />
          {Array.from({ length: 9 }, (_, i) => (
            <div key={`top-${i + 1}`} className="board-outer-coord">
              {i + 1}
            </div>
          ))}
        </div>

        <div className="board-middle">
          <div className="board-left-coords">
            {Array.from({ length: 9 }, (_, i) => (
              <div key={`left-${i + 1}`} className="board-outer-coord board-outer-coord-side">
                {i + 1}
              </div>
            ))}
          </div>

          <div className="board-grid">
            {boardData.map((row, rowIndex) =>
              row.map((piece, colIndex) => {
                const x = colIndex + 1;
                const y = rowIndex + 1;
                const key = makeCellKey(x, y);
                const highlightType = highlightedCells[key] ?? null;
                const previewPiece = previewActive
                  ? previewBoardData[rowIndex]?.[colIndex] ?? null
                  : piece;
                const previewChanged = !piecesEqual(piece, previewPiece);
                const isCannonHovered = Boolean(hoveredCannonCells[key]);
                const arrowText = arrowCells[key] ?? null;

                return (
                  <Cell
                    key={key}
                    x={x}
                    y={y}
                    piece={piece}
                    previewPiece={previewPiece}
                    previewActive={previewActive}
                    previewChanged={previewChanged}
                    coordText={makeCoordText(x, y)}
                    showCoordText={showCoordText}
                    isClickable={!isBusy}
                    isHighlighted={highlightType !== null}
                    isHovered={hoveredCellKey === key || isCannonHovered}
                    highlightType={highlightType}
                    activePlayer={activePlayer}
                    arrowText={arrowText}
                    onClick={onCellClick}
                    onHover={onCellHover}
                    onLeave={onCellLeave}
                  />
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
