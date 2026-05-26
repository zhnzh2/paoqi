import RecordPanel from "../panels/RecordPanel";
import type { GamePayload } from "../../types/game";

type GameSidebarProps = {
  compactSidebar: boolean;
  backendOk: boolean;
  initLoading: boolean;
  isSidebarBusy: boolean;
  statusMessage: string;
  statusIsError: boolean;
  payload: GamePayload | null;
  pendingAutoMessage: string;
  showRecordPanel: boolean;
  recordCollapsed: boolean;
  recordPage: number;
  totalRecordPages: number;
  pagedHistory: string[];
  recordPageSize: number;
  onNewGame: () => void;
  onRestart: () => void;
  onUndo: () => void;
  onExportRecord: () => void;
  onOpenSaveLoad: () => void;
  onOpenSettings: () => void;
  onConfirmPending: () => void;
  onToggleRecordCollapsed: () => void;
  onPrevRecordPage: () => void;
  onNextRecordPage: () => void;
};

export default function GameSidebar({
  compactSidebar,
  backendOk,
  initLoading,
  isSidebarBusy,
  statusMessage,
  statusIsError,
  payload,
  pendingAutoMessage,
  showRecordPanel,
  recordCollapsed,
  recordPage,
  totalRecordPages,
  pagedHistory,
  recordPageSize,
  onNewGame,
  onRestart,
  onUndo,
  onExportRecord,
  onOpenSaveLoad,
  onOpenSettings,
  onConfirmPending,
  onToggleRecordCollapsed,
  onPrevRecordPage,
  onNextRecordPage
}: GameSidebarProps) {
  return (
    <div className={`right-column ${compactSidebar ? "right-column-compact" : ""}`}>
      <div className="panel">
        <div className="section">
          <div><strong>后端状态：</strong>{backendOk ? "已连接" : "未连接"}</div>
          <div>
            <strong>当前提示：</strong>
            <span className={statusIsError ? "error" : "ok"}>{statusMessage}</span>
          </div>
          <div><strong>页面初始化：</strong>{initLoading ? "进行中" : "完成"}</div>
        </div>

        <div className="section button-grid">
          <button onClick={onNewGame} disabled={initLoading || isSidebarBusy}>开始新对局</button>
          <button onClick={onRestart} disabled={initLoading || isSidebarBusy}>重开</button>
          <button onClick={onUndo} disabled={initLoading || isSidebarBusy}>撤销</button>
          <button onClick={onExportRecord} disabled={initLoading || isSidebarBusy}>导出棋谱</button>
          <button onClick={onOpenSaveLoad} disabled={initLoading || isSidebarBusy}>存档</button>
          <button onClick={onOpenSettings} disabled={initLoading || isSidebarBusy}>设置</button>
        </div>

        <div className="section">
          <h2>当前局面信息</h2>
          {payload ? (
            <div className="info-grid">
              <div><strong>当前玩家：</strong>{payload.current_player}</div>
              <div><strong>当前阶段：</strong>{payload.phase}</div>
              <div><strong>回合数：</strong>{payload.turn_number}</div>
              <div><strong>游戏结束：</strong>{payload.game_over ? "是" : "否"}</div>
              <div><strong>胜方：</strong>{payload.winner ?? "无"}</div>
              <div><strong>合法动作数：</strong>{payload.legal_actions.length}</div>
              <div><strong>有待确认自动动作：</strong>{payload.has_pending_auto_action ? "是" : "否"}</div>
              <div><strong>棋谱条目数：</strong>{payload.history.length}</div>
            </div>
          ) : (
            <div>暂无数据</div>
          )}
        </div>

        {payload?.has_pending_auto_action ? (
          <div className="section">
            <div className="pending-auto-box">
              <div className="pending-auto-title">待确认自动动作</div>
              <div className="pending-auto-text">{pendingAutoMessage}</div>
              <button
                onClick={onConfirmPending}
                disabled={initLoading || isSidebarBusy}
                className="pending-auto-button"
              >
                确认自动动作
              </button>
            </div>
          </div>
        ) : null}

        {showRecordPanel ? (
          <RecordPanel
            recordCollapsed={recordCollapsed}
            recordPage={recordPage}
            totalRecordPages={totalRecordPages}
            pagedHistory={pagedHistory}
            recordPageSize={recordPageSize}
            onToggleCollapsed={onToggleRecordCollapsed}
            onPrevPage={onPrevRecordPage}
            onNextPage={onNextRecordPage}
          />
        ) : null}
      </div>
    </div>
  );
}