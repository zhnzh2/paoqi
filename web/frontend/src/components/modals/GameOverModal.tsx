import type { GamePayload } from "../../types/game";

type GameOverModalProps = {
  payload: GamePayload;
  onRestart: () => void;
  onOpenSaveLoad: () => void;
  onExportRecord: () => void;
  onBackToMenu: () => void;
};

export default function GameOverModal({
  payload,
  onRestart,
  onOpenSaveLoad,
  onExportRecord,
  onBackToMenu
}: GameOverModalProps) {
  return (
    <div className="modal-mask modal-mask-top">
      <div className="modal-card modal-card-gameover" onClick={(e) => e.stopPropagation()}>
        <div className="gameover-badge">对局结束</div>

        <div className="gameover-winner">
          {payload.winner === "R"
            ? "红方获胜"
            : payload.winner === "B"
            ? "蓝方获胜"
            : "平局"}
        </div>

        <div className="gameover-reason">
          结束原因：{payload.game_over_reason ?? "未知"}
        </div>

        <div className="gameover-summary">
          <div className="gameover-summary-item">
            <span>总回合</span>
            <strong>{payload.turn_number}</strong>
          </div>
          <div className="gameover-summary-item">
            <span>棋谱条目</span>
            <strong>{payload.history.length}</strong>
          </div>
        </div>

        <div className="modal-actions gameover-actions">
          <button onClick={onRestart}>重开</button>
          <button onClick={onOpenSaveLoad}>存档</button>
          <button onClick={onExportRecord}>导出棋谱</button>
          <button className="danger-button" onClick={onBackToMenu}>
            返回主菜单
          </button>
        </div>
      </div>
    </div>
  );
}