import { useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import UserBar from "../components/layout/UserBar";
import GameBoardSection from "../components/board/GameBoardSection";
import GameSidebar from "../components/sidebar/GameSidebar";
import SettingsModal from "../components/modals/SettingsModal";
import ConfirmModal from "../components/modals/ConfirmModal";
import GameOverModal from "../components/modals/GameOverModal";
import ChatPanel from "../components/room/ChatPanel";
import RoomInfoPanel from "../components/room/RoomInfoPanel";
import useGameViewOptions from "../hooks/ui/useGameViewOptions";
import useModalController from "../hooks/ui/useModalController";
import useModalEscapeClose from "../hooks/ui/useModalEscapeClose";
import useGameDerivedState from "../hooks/game/useGameDerivedState";
import useRoomWebSocket from "../hooks/room/useRoomWebSocket";
import useRoomGameState from "../hooks/room/useRoomGameState";
import { findActionByCell } from "../utils/gameBoardUtils";
import type { GameAction } from "../types/game";

export default function RoomGamePage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  // ------------------------------------------------------------------
  // 房间状态（WebSocket 驱动）
  // ------------------------------------------------------------------
  const {
    payload,
    playerColor,
    opponent,
    opponentConnected,
    phase,
    statusMessage,
    statusIsError,
    roomCode,
    handleWsMessage,
    setStatusMessage,
    setStatusIsError,
    chatMessages,
  } = useRoomGameState();

  const { send, isConnected, connectionState } = useRoomWebSocket({
    roomCode: code!,
    onMessage: handleWsMessage,
    onDisconnect: () => {
      setStatusMessage("连接已断开，正在重连...");
      setStatusIsError(true);
    },
  });

  // ------------------------------------------------------------------
  // UI 状态（复用现有 hooks）
  // ------------------------------------------------------------------
  const viewOptions = useGameViewOptions();
  const modal = useModalController();
  useModalEscapeClose({
    modalCount: modal.modalStack.length,
    topModal: modal.topModal,
    onCloseTopModal: () => modal.closeTopModal(),
    onCloseConfirmDialog: () => modal.closeConfirmDialog(),
  });

  const [hoveredCell, setHoveredCell] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [recordPage, setRecordPage] = useState(1);

  const derived = useGameDerivedState({
    payload,
    hoveredCell,
    recordPage,
    recordPageSize: 20,
    showDropHighlight: viewOptions.showDropHighlight,
    showEatHighlight: viewOptions.showEatHighlight,
    showMuzzleHighlight: viewOptions.showMuzzleHighlight,
    showFireHighlight: viewOptions.showFireHighlight,
    showArrowHints: viewOptions.showArrowHints,
    showCannonHoverEnhance: viewOptions.showCannonHoverEnhance,
  });

  // ------------------------------------------------------------------
  // 派生状态
  // ------------------------------------------------------------------
  const isMyTurn =
    !!payload &&
    !payload.game_over &&
    !!playerColor &&
    payload.current_player === playerColor;

  const isBoardBusy =
    connectionState !== "connected" ||
    phase === "waiting" ||
    (phase === "playing" && !isMyTurn) ||
    modal.modalStack.length > 0;

  // ------------------------------------------------------------------
  // 操作处理器
  // ------------------------------------------------------------------

  /** 棋盘格子点击 */
  const handleCellClick = useCallback(
    (x: number, y: number) => {
      if (!payload || payload.game_over || modal.modalStack.length > 0) return;
      if (!isMyTurn) {
        setStatusMessage("当前不是你的回合");
        setStatusIsError(true);
        return;
      }

      // 待确认自动动作
      if (payload.has_pending_auto_action) {
        send({ type: "game:confirm_pending" });
        setStatusMessage("已确认自动动作");
        setStatusIsError(false);
        return;
      }

      // 查找匹配的合法动作
      const action = findActionByCell(
        payload.legal_actions,
        payload.phase,
        x,
        y,
      );
      if (!action) {
        setStatusMessage("无效的操作，请重试");
        setStatusIsError(true);
        return;
      }

      send({ type: "game:action", action });
      setStatusMessage("");
      setStatusIsError(false);
    },
    [payload, isMyTurn, modal.modalStack.length, send, setStatusMessage, setStatusIsError],
  );

  const handleCellHover = useCallback(
    (x: number, y: number) => {
      setHoveredCell({ x, y });
    },
    [],
  );

  const handleCellLeave = useCallback(() => {
    setHoveredCell(null);
  }, []);

  /** 协商终局 */
  const handleEndgame = useCallback(() => {
    modal.openConfirmDialog(
      "确认终局",
      "是否确认终局？双方同意后将对当前局面进行结算。",
      "endgame",
    );
  }, [modal]);

  /** 投降 */
  const handleResign = useCallback(() => {
    modal.openConfirmDialog(
      "确认投降",
      "是否确认投降？投降后将判定对手获胜。",
      "resign",
    );
  }, [modal]);

  /** 返回主菜单 */
  const handleBackToMenu = useCallback(() => {
    modal.openConfirmDialog(
      "离开房间",
      "是否确认离开房间并返回主菜单？对局进度将会丢失。",
      "leave",
    );
  }, [modal]);

  /** 回退一步 */
  const handleUndo = useCallback(() => {
    if (!isMyTurn) {
      setStatusMessage("只能在自己的回合回退");
      setStatusIsError(true);
      return;
    }
    send({ type: "game:undo" });
    setStatusMessage("已回退一步");
    setStatusIsError(false);
  }, [isMyTurn, send, setStatusMessage, setStatusIsError]);

  /** 悔棋（回到本回合开始） */
  const handleRewind = useCallback(() => {
    if (!isMyTurn) {
      setStatusMessage("只能在自己的回合悔棋");
      setStatusIsError(true);
      return;
    }
    send({ type: "game:rewind" });
    setStatusMessage("已悔棋");
    setStatusIsError(false);
  }, [isMyTurn, send, setStatusMessage, setStatusIsError]);

  /** 导出棋谱 */
  const handleExportRecord = useCallback(() => {
    if (!payload?.history?.length) {
      setStatusMessage("暂无棋谱可导出");
      setStatusIsError(true);
      return;
    }
    const text = payload.history.join("\n");
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `paoqi-room-${code ?? "game"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    setStatusMessage("棋谱已导出");
    setStatusIsError(false);
  }, [payload, code, setStatusMessage, setStatusIsError]);

  /** 离开房间返回菜单 */
  const handleLeaveRoom = useCallback(() => {
    navigate("/", { replace: true });
  }, [navigate]);

  /** 发送聊天消息 */
  const handleSendChat = useCallback(
    (text: string) => {
      send({ type: "chat:send", text });
    },
    [send],
  );

  /** 确认对话框回调 */
  const handleConfirmAction = useCallback(
    (action: string) => {
      switch (action) {
        case "endgame":
          send({ type: "game:endgame" });
          setStatusMessage("已请求终局");
          setStatusIsError(false);
          break;
        case "resign":
          send({ type: "game:resign" });
          setStatusMessage("已投降");
          setStatusIsError(false);
          break;
        case "leave":
          handleLeaveRoom();
          break;
      }
      modal.closeConfirmDialog();
    },
    [send, modal, handleLeaveRoom, setStatusMessage, setStatusIsError],
  );

  // ------------------------------------------------------------------
  // 渲染
  // ------------------------------------------------------------------

  const displayRoomCode = roomCode || code || "??????";

  return (
    <div className="room-game-page">
      <UserBar />

      {/* 顶部信息栏（极简：仅标题 + 房间码，详细状态在侧边栏 RoomInfoPanel） */}
      <div className="room-info-bar">
        <span className="room-info-bar-title">房间对战</span>
        <span
          className="room-info-bar-code"
          title="点击复制房间码"
          onClick={() => {
            navigator.clipboard.writeText(displayRoomCode).then(() => {
              setStatusMessage("房间码已复制到剪贴板");
              setStatusIsError(false);
            });
          }}
        >
          {displayRoomCode}
        </span>
        {!isConnected ? (
          <span className="room-info-disconnected">断开</span>
        ) : null}
      </div>

      {/* 等待对手界面 */}
      {phase === "waiting" ? (
        <div className="room-waiting">
          <div className="room-waiting-card">
            <h2>等待对手加入</h2>
            <p className="room-waiting-code">
              房间码：<strong>{displayRoomCode}</strong>
            </p>
            <p className="room-waiting-hint">
              将房间码分享给好友，或让好友在房间列表中查找此房间
            </p>
            <button
              className="room-waiting-copy"
              onClick={() => {
                navigator.clipboard.writeText(displayRoomCode);
              }}
            >
              复制房间码
            </button>
            <button
              className="room-waiting-leave"
              onClick={() => navigate("/rooms")}
            >
              返回房间列表
            </button>
          </div>
        </div>
      ) : (
        /* 游戏界面 */
        <div className="layout">
          <GameBoardSection
            boardData={derived.boardData}
            previewBoardData={null}
            highlightedCells={derived.highlightedCells}
            hoveredCellKey={derived.hoveredCellKey}
            hoveredCannonCells={derived.hoveredCannonCells}
            arrowCells={derived.arrowCells}
            activePlayer={payload?.current_player ?? null}
            showCoordText={viewOptions.showCoordInsideCell}
            isBusy={isBoardBusy}
            dangerDisabled={!payload || payload.game_over}
            onCellClick={handleCellClick}
            onCellHover={handleCellHover}
            onCellLeave={handleCellLeave}
            onEndgame={handleEndgame}
            onResign={handleResign}
            onBackToMenu={handleBackToMenu}
            title="房间对战"
          />

          <GameSidebar
            compactSidebar={viewOptions.compactSidebar}
            backendOk={isConnected}
            initLoading={connectionState === "connecting"}
            isSidebarBusy={connectionState !== "connected"}
            statusMessage={statusMessage}
            statusIsError={statusIsError}
            payload={payload}
            pendingAutoMessage={
              payload?.pending_auto_message ?? ""
            }
            showRecordPanel={viewOptions.showRecordPanel}
            recordCollapsed={viewOptions.recordCollapsed}
            recordPage={recordPage}
            totalRecordPages={derived.totalRecordPages}
            pagedHistory={derived.pagedHistory}
            recordPageSize={20}
            onNewGame={handleLeaveRoom}
            onRestart={() => {}}
            onUndo={handleUndo}
            onRewind={handleRewind}
            onExportRecord={handleExportRecord}
            onOpenSaveLoad={() => {
              setStatusMessage("联机模式不支持存档功能");
              setStatusIsError(true);
            }}
            onOpenSettings={() => modal.openModal("settings")}
            onConfirmPending={() => {
              send({ type: "game:confirm_pending" });
            }}
            onToggleRecordCollapsed={() =>
              viewOptions.setRecordCollapsed(!viewOptions.recordCollapsed)
            }
            onPrevRecordPage={() =>
              setRecordPage((p) => Math.max(1, p - 1))
            }
            onNextRecordPage={() =>
              setRecordPage((p) =>
                Math.min(derived.totalRecordPages, p + 1),
              )
            }
            hideRestart
            hideSaveLoad
            chatSlot={
              <ChatPanel
                messages={chatMessages}
                myColor={playerColor}
                onSend={handleSendChat}
                disabled={!isConnected}
              />
            }
            roomInfoSlot={
              viewOptions.showRoomInfo ? (
                <RoomInfoPanel
                  roomCode={displayRoomCode}
                  redName={
                    playerColor === "R"
                      ? "你"
                      : opponent?.username ?? null
                  }
                  blueName={
                    playerColor === "B"
                      ? "你"
                      : opponent?.username ?? null
                  }
                  redConnected={
                    playerColor === "R" ? isConnected : opponentConnected
                  }
                  blueConnected={
                    playerColor === "B" ? isConnected : opponentConnected
                  }
                  myColor={playerColor}
                  isMyTurn={isMyTurn}
                  phase={phase}
                  isConnected={isConnected}
                />
              ) : null
            }
          />

          {/* 游戏结束模态框 */}
          {payload?.game_over ? (
            <GameOverModal
              payload={payload}
              onRestart={() => {
                send({ type: "game:restart" });
                setStatusMessage("已请求再来一局");
                setStatusIsError(false);
              }}
              onOpenSaveLoad={() => {
                setStatusMessage("联机模式不支持存档功能");
                setStatusIsError(true);
              }}
              onExportRecord={handleExportRecord}
              onBackToMenu={handleLeaveRoom}
            />
          ) : null}
        </div>
      )}

      {/* 全局模态框 */}
      {modal.isModalOpen("settings") ? (
        <SettingsModal
          isTop={modal.topModal === "settings"}
          showRecordPanel={viewOptions.showRecordPanel}
          showCoordInsideCell={viewOptions.showCoordInsideCell}
          compactSidebar={viewOptions.compactSidebar}
          showDropHighlight={viewOptions.showDropHighlight}
          showEatHighlight={viewOptions.showEatHighlight}
          showMuzzleHighlight={viewOptions.showMuzzleHighlight}
          showFireHighlight={viewOptions.showFireHighlight}
          showArrowHints={viewOptions.showArrowHints}
          showHoverPreview={viewOptions.showHoverPreview}
          showCannonHoverEnhance={viewOptions.showCannonHoverEnhance}
          showRoomInfo={viewOptions.showRoomInfo}
          onCloseTop={() => modal.closeTopModal()}
          onCloseDirect={() => modal.closeModal("settings")}
          onChangeShowRecordPanel={viewOptions.setShowRecordPanel}
          onChangeShowCoordInsideCell={viewOptions.setShowCoordInsideCell}
          onChangeCompactSidebar={viewOptions.setCompactSidebar}
          onChangeShowDropHighlight={viewOptions.setShowDropHighlight}
          onChangeShowEatHighlight={viewOptions.setShowEatHighlight}
          onChangeShowMuzzleHighlight={viewOptions.setShowMuzzleHighlight}
          onChangeShowFireHighlight={viewOptions.setShowFireHighlight}
          onChangeShowArrowHints={viewOptions.setShowArrowHints}
          onChangeShowHoverPreview={viewOptions.setShowHoverPreview}
          onChangeShowCannonHoverEnhance={viewOptions.setShowCannonHoverEnhance}
          onChangeShowRoomInfo={viewOptions.setShowRoomInfo}
        />
      ) : null}

      {modal.confirmDialog ? (
        <ConfirmModal
          isTop={modal.topModal === "confirm"}
          title={modal.confirmDialog.title}
          message={modal.confirmDialog.message}
          onCloseTop={() => modal.closeTopModal()}
          onConfirm={() =>
            handleConfirmAction(modal.confirmDialog?.action ?? "leave")
          }
          onCancel={() => modal.closeConfirmDialog()}
        />
      ) : null}
    </div>
  );
}
