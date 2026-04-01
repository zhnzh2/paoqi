type PieceProps = {
  color: "R" | "B";
  level: number;
};

export default function Piece({ color, level }: PieceProps) {
  return (
    <div className={`piece ${color === "R" ? "piece-red" : "piece-blue"}`}>
      <span className="piece-level">{level}</span>
    </div>
  );
}