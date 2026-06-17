import { Routes, Route, Navigate, useSearchParams } from "react-router-dom";
import { EngineProvider, useEngine, EngineLoadingScreen } from "./engine/EngineContext";
import { useAuth } from "./auth/AuthContext";
import GamePage from "./pages/GamePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import UserPage from "./pages/UserPage";
import MenuPage from "./components/menu/MenuPage";
import ComingSoonPage from "./pages/ComingSoonPage";
import RoomListPage from "./pages/RoomListPage";
import RoomGamePage from "./pages/RoomGamePage";

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
 * 路由守卫：未认证用户重定向到登录页。
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAuthLoading } = useAuth();

  if (isAuthLoading) {
    return (
      <div
        className="page"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          color: "#ccc",
        }}
      >
        加载中...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

/**
 * 应用根组件。
 */
export default function App() {
  return (
    <Routes>
      {/* 公开路由 */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* 受保护路由 */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MenuPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/user/:uid"
        element={
          <ProtectedRoute>
            <UserPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/local"
        element={
          <ProtectedRoute>
            <LocalGameRoute />
          </ProtectedRoute>
        }
      />
      <Route
        path="/rooms"
        element={
          <ProtectedRoute>
            <RoomListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/room/:code"
        element={
          <ProtectedRoute>
            <RoomGamePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/online"
        element={
          <ProtectedRoute>
            <RoomListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai"
        element={
          <ProtectedRoute>
            <ComingSoonPage mode="AI 对战" />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
