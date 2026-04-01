import { useEffect, useState } from "react";
import { getSaveSlots } from "./api/gameApi";
import GamePage from "./pages/GamePage";
import MenuPage from "./components/menu/MenuPage";

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
    return (
      <MenuPage
        menuMeta={menuMeta}
        menuLoading={menuLoading}
        onStartGame={() => {
          setOpenLoadOnEnter(false);
          setAppMode("game");
        }}
        onContinueGame={() => {
          setOpenLoadOnEnter(false);
          setAppMode("game");
        }}
        onLoadGame={() => {
          setOpenLoadOnEnter(true);
          setAppMode("game");
        }}
      />
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