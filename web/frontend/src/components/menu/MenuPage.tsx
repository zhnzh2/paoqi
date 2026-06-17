import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const LS_CURRENT_GAME = "paoqi_current_game";

type MenuMeta = {
  can_continue: boolean;
};

function buildMenuMeta(): MenuMeta {
  let can_continue = false;
  const raw = localStorage.getItem(LS_CURRENT_GAME);
  if (raw) {
    try {
      const data = JSON.parse(raw);
      const historyLen = data.history?.length ?? 0;
      const gameOver = data.game_over ?? false;
      can_continue = historyLen > 0 && !gameOver;
    } catch {
      // 损坏数据，忽略
    }
  }
  return { can_continue };
}

export default function MenuPage() {
  const navigate = useNavigate();
  const [menuMeta, setMenuMeta] = useState<MenuMeta>({ can_continue: false });

  useEffect(() => {
    setMenuMeta(buildMenuMeta());
  }, []);

  return (
    <div className="menu-page">
      <div className="menu-header">
        <h1 className="menu-title">炮棋</h1>
        <p className="menu-subtitle">选择游戏模式，开始对局</p>
      </div>

      <div className="mode-grid">
        {/* 单机模式 — 已上线 */}
        <div className="mode-card mode-card-active">
          <div className="mode-status">
            <span className="mode-badge mode-badge-live">已上线</span>
          </div>
          <h2 className="mode-name">单机模式</h2>
          <p className="mode-desc">
            本地浏览器直接运行，无需联网。
            <br />
            支持完整规则、存档读档、棋谱导出。
          </p>
          <div className="mode-actions">
            <button
              className="mode-button mode-button-primary"
              onClick={() => {
                localStorage.removeItem(LS_CURRENT_GAME);
                navigate("/local");
              }}
            >
              进入模式
            </button>
            {menuMeta.can_continue ? (
              <button
                className="mode-button mode-button-ghost"
                onClick={() => navigate("/local")}
              >
                继续上次对局
              </button>
            ) : null}
          </div>
        </div>

        {/* 联机模式 — 开发中 */}
        <div className="mode-card mode-card-disabled">
          <div className="mode-status">
            <span className="mode-badge mode-badge-dev">开发中</span>
          </div>
          <h2 className="mode-name">联机模式</h2>
          <p className="mode-desc">
            在线匹配，与好友实时对弈。
            <br />
            支持房间创建、加入和观战功能。
          </p>
          <div className="mode-actions">
            <button className="mode-button mode-button-disabled" disabled>
              敬请期待
            </button>
          </div>
        </div>
      </div>

      {/* 下方居中 */}
      <div className="mode-grid-bottom">
        <div className="mode-card mode-card-disabled">
          <div className="mode-status">
            <span className="mode-badge mode-badge-dev">开发中</span>
          </div>
          <h2 className="mode-name">AI 对战</h2>
          <p className="mode-desc">
            与训练好的炮棋 AI 对弈。
            <br />
            支持多难度选择与棋局分析。
          </p>
          <div className="mode-actions">
            <button className="mode-button mode-button-disabled" disabled>
              敬请期待
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
