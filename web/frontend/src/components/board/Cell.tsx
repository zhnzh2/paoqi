import Piece from "./Piece";

type PieceData = {
  color: "R" | "B";
  level: number;
} | null;

type CellProps = {
  x: number;
  y: number;
  piece: PieceData;
  previewPiece: PieceData;
  coordText: string;
  showCoordText: boolean;
  isClickable: boolean;
  isHighlighted: boolean;
  isHovered: boolean;
  highlightType: "drop" | "eat" | "muzzle" | "fire" | null;
  activePlayer: "R" | "B" | null;
  arrowText: string | null;
  onClick: (x: number, y: number) => void | Promise<void>;
  onHover: (x: number, y: number) => void;
  onLeave: () => void;
};

export default function Cell({
  x,
  y,
  piece,
  previewPiece,
  coordText,
  showCoordText,
  isClickable,
  isHighlighted,
  isHovered,
  highlightType,
  activePlayer,
  arrowText,
  onClick,
  onHover,
  onLeave
}: CellProps) {
  let highlightClass = "";

  if (isHighlighted && highlightType) {
    if (highlightType === "drop") {
      highlightClass = "board-cell-highlight-drop";
    } else if (highlightType === "muzzle") {
      highlightClass = "board-cell-highlight-muzzle";
    } else if (highlightType === "fire") {
      highlightClass =
        activePlayer === "R"
          ? "board-cell-highlight-fire-red"
          : "board-cell-highlight-fire-blue";
    } else if (highlightType === "eat") {
      highlightClass =
        activePlayer === "R"
          ? "board-cell-highlight-eat-red"
          : "board-cell-highlight-eat-blue";
    }
  }

  const hoverClass = isHovered ? "board-cell-hovered" : "";
  const displayPiece = previewPiece ?? piece;
  const showPreview = previewPiece !== null;

  return (
    <button
      type="button"
      className={`board-cell ${isClickable ? "board-cell-clickable" : ""} ${highlightClass} ${hoverClass}`}
      onClick={() => onClick(x, y)}
      onMouseEnter={() => onHover(x, y)}
      onMouseLeave={onLeave}
    >
      {showCoordText ? <div className="cell-coord">{coordText}</div> : null}

      {arrowText ? <div className="cell-arrow">{arrowText}</div> : null}

      <div className="cell-piece-wrap">
        {displayPiece ? (
          <div className={showPreview ? "piece-preview-wrap" : ""}>
            <Piece color={displayPiece.color} level={displayPiece.level} />
          </div>
        ) : null}
      </div>
    </button>
  );
}