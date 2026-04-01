type DangerActionsPanelProps = {
  disabled: boolean;
  onEndgame: () => void;
  onResign: () => void;
  onBackToMenu: () => void;
};

export default function DangerActionsPanel({
  disabled,
  onEndgame,
  onResign,
  onBackToMenu
}: DangerActionsPanelProps) {
  return (
    <div className="danger-actions-panel board-danger-panel">
      <div className="danger-actions-title">危险操作</div>

      <div className="danger-actions-row">
        <button
          className="danger-button"
          onClick={onEndgame}
          disabled={disabled}
        >
          协商终局
        </button>

        <button
          className="danger-button"
          onClick={onResign}
          disabled={disabled}
        >
          投降
        </button>
      </div>

      <div className="danger-actions-row danger-actions-row-bottom">
        <button
          className="danger-button danger-actions-wide"
          onClick={onBackToMenu}
          disabled={disabled}
        >
          返回主菜单
        </button>
      </div>
    </div>
  );
}