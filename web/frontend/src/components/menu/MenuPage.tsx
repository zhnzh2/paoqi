type MenuMeta = {
  can_continue: boolean;
  slots: Array<{
    slot: number;
    exists: boolean;
    updated_at: number | null;
  }>;
  game_over: boolean;
  history_count: number;
};

type MenuPageProps = {
  menuMeta: MenuMeta | null;
  menuLoading: boolean;
  onStartGame: () => void;
  onContinueGame: () => void;
  onLoadGame: () => void;
};

export default function MenuPage({
  menuMeta,
  menuLoading,
  onStartGame,
  onContinueGame,
  onLoadGame
}: MenuPageProps) {
  const hasAnySave = Boolean(menuMeta?.slots?.some((slot) => slot.exists));
  const canContinue = Boolean(menuMeta?.can_continue);

  return (
    <div className="menu-page">
      <div className="menu-card">
        <div className="menu-title">炮棋</div>
        <div className="menu-subtitle">Web 单机版原型</div>

        <div className="menu-actions">
          <button
            className="menu-button menu-button-primary"
            onClick={onStartGame}
          >
            开始游戏
          </button>

          <button
            className="menu-button menu-button-secondary"
            disabled={menuLoading || !canContinue}
            onClick={onContinueGame}
          >
            继续对局
          </button>

          <button
            className="menu-button menu-button-secondary"
            disabled={menuLoading || !hasAnySave}
            onClick={onLoadGame}
          >
            读取存档
          </button>
        </div>
      </div>
    </div>
  );
}