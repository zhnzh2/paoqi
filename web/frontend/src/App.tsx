import { useEffect, useState } from "react";
import { getSaveSlots } from "./api/gameApi";
import GamePage from "./pages/GamePage";

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

export default function App() {
  const [appMode, setAppMode] = useState<"menu" | "game">("menu");
  const [menuMeta, setMenuMeta] = useState<MenuMeta | null>(null);
  const [menuLoading, setMenuLoading] = useState<boolean>(true);
  const [openLoadOnEnter, setOpenLoadOnEnter] = useState<boolean>(false);

  async function refreshMenuMeta() {
    setMenuLoading(true);
    try {
      const res = await getSaveSlots();
      if (res.ok) {
        setMenuMeta(res.data);
      }
    } finally {
      setMenuLoading(false);
    }
  }

  useEffect(() => {
    refreshMenuMeta();
  }, []);

  if (appMode === "menu") {
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
              onClick={() => {
                setOpenLoadOnEnter(false);
                setAppMode("game");
              }}
            >
              开始游戏
            </button>

            <button
              className="menu-button menu-button-secordary"
              disabled={menuLoading || !canContinue}
              onClick={() => {
                setOpenLoadOnEnter(false);
                setAppMode("game");
              }}
            >
              继续对局
            </button>

            <button
              className="menu-button menu-button-secordary"
              disabled={menuLoading || !hasAnySave}
              onClick={() => {
                setOpenLoadOnEnter(true);
                setAppMode("game");
              }}
            >
              读取存档
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <GamePage
      onBackToMenu={async () => {
        await refreshMenuMeta();
        setAppMode("menu");
      }}
      openLoadModalOnMount={openLoadOnEnter}
    />
  );
}