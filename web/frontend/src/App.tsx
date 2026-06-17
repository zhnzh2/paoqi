import { Routes, Route, Navigate, useSearchParams } from "react-router-dom";
import { EngineProvider, useEngine, EngineLoadingScreen } from "./engine/EngineContext";
import GamePage from "./pages/GamePage";
import MenuPage from "./components/menu/MenuPage";
import ComingSoonPage from "./pages/ComingSoonPage";

/**
 * GamePage 的薄包装，从 URL search params 读取初始参数。
 * 例如 /local?load=1 表示挂载后自动打开读档弹窗。
 */
function GamePageWrapper() {
  const [searchParams] = useSearchParams();
  const openLoadModalOnMount = searchParams.get("load") === "1";
  return <GamePage openLoadModalOnMount={openLoadModalOnMount} />;
}

/**
 * 单机对局路由 —— 只有进入本地对局时才加载 Pyodide 引擎。
 */
function LocalGameRoute() {
  return (
    <EngineProvider>
      <LocalGameContent />
    </EngineProvider>
  );
}

function LocalGameContent() {
  const { isLoading, errorMessage } = useEngine();

  if (isLoading || errorMessage) {
    return <EngineLoadingScreen />;
  }

  return <GamePageWrapper />;
}

/**
 * 应用根组件。
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MenuPage />} />
      <Route path="/local" element={<LocalGameRoute />} />
      <Route path="/online" element={<ComingSoonPage mode="联机模式" />} />
      <Route path="/ai" element={<ComingSoonPage mode="AI 对战" />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
