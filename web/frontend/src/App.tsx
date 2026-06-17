import { useEffect, useState } from "react";
import { EngineProvider, useEngine, EngineLoadingScreen } from "./engine/EngineContext";
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

const LS_CURRENT_GAME = "paoqi_current_game";
const LS_SAVE_SLOT_PREFIX = "paoqi_save_slot_";

function buildLocalMenuMeta(): MenuMeta {
  let can_continue = false;
  let game_over = false;
  let history_count = 0;

  const currentRaw = localStorage.getItem(LS_CURRENT_GAME);
  if (currentRaw) {
    try {
      const data = JSON.parse(currentRaw);
      history_count = data.history?.length ?? 0;
      game_over = data.game_over ?? false;
      can_continue = history_count > 0 && !game_over;
    } catch {
      // 损坏数据，忽略
    }
  }

  const slots = [1, 2, 3].map((slot) => {
    const raw = localStorage.getItem(`${LS_SAVE_SLOT_PREFIX}${slot}`);
    return {
      slot,
      exists: raw !== null,
      updated_at: null,
    };
  });

  return { can_continue, slots, game_over, history_count };
}

/**
 * 内部组件 —— EngineProvider 加载完成后再渲染。
 * 引擎未就绪时显示 EngineLoadingScreen（含进度条/错误/重试按钮）。
 */
function AppInner() {
  const { isReady, isLoading, errorMessage } = useEngine();
  const [appMode, setAppMode] = useState<"menu" | "game">("menu");
  const [menuMeta, setMenuMeta] = useState<MenuMeta>(buildLocalMenuMeta());
  const [menuLoading, setMenuLoading] = useState<boolean>(true);
  const [openLoadOnEnter, setOpenLoadOnEnter] = useState<boolean>(false);

  function refreshMenuMeta() {
    setMenuLoading(true);
    setMenuMeta(buildLocalMenuMeta());
    setMenuLoading(false);
  }

  useEffect(() => {
    refreshMenuMeta();
  }, []);

  useEffect(() => {
    if (isReady) {
      setMenuLoading(false);
      refreshMenuMeta();
    }
  }, [isReady]);

  // 引擎加载中或出错 → 显示加载界面（含进度条 / 错误信息 / 重试按钮）
  if (isLoading || errorMessage) {
    return <EngineLoadingScreen />;
  }

  if (appMode === "menu") {
    return (
      <MenuPage
        menuMeta={menuMeta}
        menuLoading={menuLoading}
        onStartGame={() => {
          localStorage.removeItem(LS_CURRENT_GAME);
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
        refreshMenuMeta();
        setAppMode("menu");
      }}
      openLoadModalOnMount={openLoadOnEnter}
    />
  );
}

/**
 * 应用根组件。
 * EngineProvider 在最外层，确保引擎初始化只执行一次。
 */
export default function App() {
  return (
    <EngineProvider>
      <AppInner />
    </EngineProvider>
  );
}
