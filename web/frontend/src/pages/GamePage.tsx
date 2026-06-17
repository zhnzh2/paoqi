import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useEngine } from "../engine/EngineContext";
import type { GamePayload } from "../types/game";
import ConfirmModal from "../components/modals/ConfirmModal";
import GameBoardSection from "../components/board/GameBoardSection";
import GameOverModal from "../components/modals/GameOverModal";
import GameSidebar from "../components/sidebar/GameSidebar";
import SaveLoadModal from "../components/modals/SaveLoadModal";
import SettingsModal from "../components/modals/SettingsModal";
import useBoardInteractionHandlers from "../hooks/game/useBoardInteractionHandlers";
import useGameActionRunner from "../hooks/game/useGameActionRunner";
import useGameDerivedState from "../hooks/game/useGameDerivedState";
import useGameLifecycle from "../hooks/game/useGameLifecycle";
import useHoverPreview from "../hooks/game/useHoverPreview";
import useGameViewOptions from "../hooks/ui/useGameViewOptions";
import useModalController from "../hooks/ui/useModalController";
import useModalEscapeClose from "../hooks/ui/useModalEscapeClose";

// localStorage 键名
const LS_CURRENT_GAME = "paoqi_current_game";
const LS_SAVE_SLOT_PREFIX = "paoqi_save_slot_";

type GamePageProps = {
  openLoadModalOnMount?: boolean;
};

export default function GamePage({ openLoadModalOnMount = false }: GamePageProps) {
  const navigate = useNavigate();
  const { engine, isReady } = useEngine();

  const [payload, setPayload] = useState<GamePayload | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("引擎就绪，对局已开始。");
  const [statusIsError, setStatusIsError] = useState<boolean>(false);
  const [hoveredCell, setHoveredCell] = useState<{ x: number; y: number } | null>(null);
  const [recordPage, setRecordPage] = useState<number>(1);
  const recordPageSize = 20;

  // 自动保存去重：跟踪上次写入的完整导出状态
  const lastSavedState = useRef<string | null>(null);

  const {
    showRecordPanel,
    setShowRecordPanel,
    showCoordInsideCell,
    setShowCoordInsideCell,
    showDropHighlight,
    setShowDropHighlight,
    showEatHighlight,
    setShowEatHighlight,
    showMuzzleHighlight,
    setShowMuzzleHighlight,
    showFireHighlight,
    setShowFireHighlight,
    showArrowHints,
    setShowArrowHints,
    showHoverPreview,
    setShowHoverPreview,
    showCannonHoverEnhance,
    setShowCannonHoverEnhance,
    compactSidebar,
    setCompactSidebar,
    recordCollapsed,
    setRecordCollapsed
  } = useGameViewOptions();

  const {
    modalStack,
    confirmDialog,
    openModal,
    closeModal,
    closeTopModal,
    isModalOpen,
    topModal,
    openConfirmDialog,
    closeConfirmDialog
  } = useModalController();

  const {
    busyScope,
    isBoardBusy,
    isSidebarBusy,
    runAction
  } = useGameActionRunner({
    onSuccessPayload: (p: GamePayload) => {
      setPayload(p);
      autoSave(p);
    },
    onStatusMessage: setStatusMessage,
    onStatusIsError: setStatusIsError
  });

  const {
    handleBoardCellClick,
    handleBoardCellHover,
    handleBoardCellLeave
  } = useBoardInteractionHandlers({
    payload,
    isBoardBusy,
    modalCount: modalStack.length,
    onStatusMessage: setStatusMessage,
    onStatusIsError: setStatusIsError,
    onHoveredCellChange: setHoveredCell,
    onPayloadChange: (p: GamePayload) => {
      setPayload(p);
      autoSave(p);
    }
  });

  const {
    totalRecordPages,
    pagedHistory,
    boardData,
    highlightedCells,
    hoveredCellKey,
    hoveredCannonCells,
    arrowCells,
    pendingAutoMessage
  } = useGameDerivedState({
    payload,
    hoveredCell,
    recordPage,
    recordPageSize,
    showDropHighlight,
    showEatHighlight,
    showMuzzleHighlight,
    showFireHighlight,
    showArrowHints,
    showCannonHoverEnhance
  });

  const { previewBoardData } = useHoverPreview({
    payload,
    hoveredCell,
    busyScope,
    modalCount: modalStack.length,
    showHoverPreview
  });

  useGameLifecycle({
    openLoadModalOnMount,
    payload,
    recordPage,
    totalRecordPages,
    onOpenModal: openModal,
    onHoveredCellClear: () => setHoveredCell(null),
    onPayloadChange: (p: GamePayload) => {
      setPayload(p);
      autoSave(p);
    },
    onStatusMessage: setStatusMessage,
    onStatusIsError: setStatusIsError,
    onRecordPageChange: setRecordPage
  });

  useModalEscapeClose({
    modalCount: modalStack.length,
    topModal,
    onCloseTopModal: closeTopModal,
    onCloseConfirmDialog: closeConfirmDialog
  });

  // ===================== 自动保存 =====================

  function autoSave(p: GamePayload) {
    if (!engine || !isReady) return;

    const shouldRemember = (p.history?.length ?? 0) > 0 || Boolean(p.game_over);
    if (!shouldRemember) {
      lastSavedState.current = null;
      localStorage.removeItem(LS_CURRENT_GAME);
      return;
    }

    try {
      const state = engine.exportState();
      const serialized = JSON.stringify(state);
      if (serialized === lastSavedState.current) return;
      lastSavedState.current = serialized;
      localStorage.setItem(LS_CURRENT_GAME, serialized);
    } catch {
      // localStorage 写入失败（存储满等），静默忽略
    }
  }

  // ===================== 引擎操作方法 =====================

  const runEngineOp = useCallback(
    (op: () => any) => runAction(op, "sidebar"),
    [runAction]
  );

  const handleNewGame = useCallback(() => {
    if (!engine) return;
    runEngineOp(() => {
      const p = engine.newGame();
      lastSavedState.current = null;
      localStorage.removeItem(LS_CURRENT_GAME);
      return { ok: true, message: "已开始新对局。", payload: p };
    });
  }, [engine, runEngineOp]);

  const handleRestart = useCallback(() => {
    openConfirmDialog("确认重开", "是否确认重新开始当前对局？", "restart");
  }, [openConfirmDialog]);

  const handleUndo = useCallback(() => {
    if (!engine) return;
    runEngineOp(() => engine.undo());
  }, [engine, runEngineOp]);

  const handleConfirmPending = useCallback(() => {
    if (!engine) return;
    runEngineOp(() => engine.confirmPending());
  }, [engine, runEngineOp]);

  const handleEndGame = useCallback(() => {
    openConfirmDialog(
      "确认终局",
      "是否确认双方同意结束当前对局？\n系统将按当前局面计算胜负。",
      "endgame"
    );
  }, [openConfirmDialog]);

  const handleResign = useCallback(() => {
    openConfirmDialog(
      "确认投降",
      "是否确认当前行动方投降？\n确认后将直接判负。",
      "resign"
    );
  }, [openConfirmDialog]);

  // ===================== 存档操作 =====================

  const getSaveSlotKey = (slot: number) => `${LS_SAVE_SLOT_PREFIX}${slot}`;

  const handleSave = useCallback(
    (slot: number) => {
      if (!engine) return;
      runEngineOp(() => {
        const state = engine.exportState();
        localStorage.setItem(getSaveSlotKey(slot), JSON.stringify(state));
        return { ok: true, message: `已保存到槽位 ${slot}。`, payload: engine.getPayload() };
      });
    },
    [engine, runEngineOp]
  );

  const handleLoad = useCallback(
    (slot: number) => {
      if (!engine) return;
      runEngineOp(() => {
        const raw = localStorage.getItem(getSaveSlotKey(slot));
        if (!raw) {
          return { ok: false, message: `槽位 ${slot} 没有存档。` };
        }
        try {
          const data = JSON.parse(raw);
          const p = engine.importState(data);
          return { ok: true, message: `已从槽位 ${slot} 载入对局。`, payload: p };
        } catch {
          return { ok: false, message: "存档数据损坏，无法读取。" };
        }
      });
    },
    [engine, runEngineOp]
  );

  const handleExportRecord = useCallback(() => {
    if (!engine) return;
    runEngineOp(() => {
      const p = engine.getPayload();
      const text = (p.history ?? []).join("\n");
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "paoqi_record.txt";
      a.click();
      URL.revokeObjectURL(url);
      return { ok: true, message: "棋谱已导出。", payload: p };
    });
  }, [engine, runEngineOp]);

  // ===================== 确认对话框回调 =====================

  const handleConfirmAction = useCallback(async () => {
    if (!confirmDialog || !engine) return;
    const action = confirmDialog.action;
    closeConfirmDialog();

    switch (action) {
      case "save1":
        handleSave(1);
        break;
      case "save2":
        handleSave(2);
        break;
      case "save3":
        handleSave(3);
        break;
      case "load1":
        handleLoad(1);
        break;
      case "load2":
        handleLoad(2);
        break;
      case "load3":
        handleLoad(3);
        break;
      case "restart":
        runEngineOp(() => {
          const p = engine.restart();
          lastSavedState.current = null;
          localStorage.removeItem(LS_CURRENT_GAME);
          return { ok: true, message: "已重新开始对局。", payload: p };
        });
        break;
      case "confirm-pending":
        handleConfirmPending();
        break;
      case "endgame":
        runEngineOp(() => engine.endGameByAgreement());
        break;
      case "resign":
        runEngineOp(() => engine.resign());
        break;
    }
  }, [confirmDialog, engine, closeConfirmDialog, handleSave, handleLoad, runEngineOp, handleConfirmPending]);

  // 引擎由 App 层统一加载，到这里时已经就绪。
  // payload 在 useGameLifecycle 中初始化，极短间隙显示占位。
  if (!payload) {
    return (
      <div className="page">
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          color: "#ccc",
          fontFamily: "sans-serif",
          background: "#1a1a1a",
        }}>
          正在准备对局…
        </div>
      </div>
    );
  }

  // ===================== 正常游戏界面 =====================

  return (
    <div className="page">
      <div className="layout">
        <GameBoardSection
          boardData={boardData}
          previewBoardData={previewBoardData}
          highlightedCells={highlightedCells}
          hoveredCellKey={hoveredCellKey}
          hoveredCannonCells={hoveredCannonCells}
          arrowCells={arrowCells}
          activePlayer={payload?.current_player ?? null}
          showCoordText={showCoordInsideCell}
          isBusy={isBoardBusy || modalStack.length > 0 || Boolean(payload?.game_over)}
          dangerDisabled={isSidebarBusy}
          onCellClick={handleBoardCellClick}
          onCellHover={handleBoardCellHover}
          onCellLeave={handleBoardCellLeave}
          onEndgame={handleEndGame}
          onResign={handleResign}
          onBackToMenu={() => navigate("/")}
        />

        <GameSidebar
          compactSidebar={compactSidebar}
          backendOk={true}
          initLoading={false}
          isSidebarBusy={isSidebarBusy}
          statusMessage={statusMessage}
          statusIsError={statusIsError}
          payload={payload}
          pendingAutoMessage={pendingAutoMessage}
          showRecordPanel={showRecordPanel}
          recordCollapsed={recordCollapsed}
          recordPage={recordPage}
          totalRecordPages={totalRecordPages}
          pagedHistory={pagedHistory}
          recordPageSize={recordPageSize}
          onNewGame={handleNewGame}
          onRestart={handleRestart}
          onUndo={handleUndo}
          onExportRecord={handleExportRecord}
          onOpenSaveLoad={() => openModal("save-load")}
          onOpenSettings={() => openModal("settings")}
          onConfirmPending={handleConfirmPending}
          onToggleRecordCollapsed={() => setRecordCollapsed((prev) => !prev)}
          onPrevRecordPage={() => setRecordPage((p) => Math.max(1, p - 1))}
          onNextRecordPage={() => setRecordPage((p) => Math.min(totalRecordPages, p + 1))}
        />

        {modalStack.length > 0 ? (
          <div className="modal-overlay-root">
            {isModalOpen("settings") ? (
              <SettingsModal
                isTop={topModal === "settings"}
                showRecordPanel={showRecordPanel}
                showCoordInsideCell={showCoordInsideCell}
                compactSidebar={compactSidebar}
                showDropHighlight={showDropHighlight}
                showEatHighlight={showEatHighlight}
                showMuzzleHighlight={showMuzzleHighlight}
                showFireHighlight={showFireHighlight}
                showArrowHints={showArrowHints}
                showHoverPreview={showHoverPreview}
                showCannonHoverEnhance={showCannonHoverEnhance}
                onCloseTop={closeTopModal}
                onCloseDirect={() => closeModal("settings")}
                onChangeShowRecordPanel={setShowRecordPanel}
                onChangeShowCoordInsideCell={setShowCoordInsideCell}
                onChangeCompactSidebar={setCompactSidebar}
                onChangeShowDropHighlight={setShowDropHighlight}
                onChangeShowEatHighlight={setShowEatHighlight}
                onChangeShowMuzzleHighlight={setShowMuzzleHighlight}
                onChangeShowFireHighlight={setShowFireHighlight}
                onChangeShowArrowHints={setShowArrowHints}
                onChangeShowHoverPreview={setShowHoverPreview}
                onChangeShowCannonHoverEnhance={setShowCannonHoverEnhance}
              />
            ) : null}

            {isModalOpen("save-load") ? (
              <SaveLoadModal
                isTop={topModal === "save-load"}
                onCloseTop={closeTopModal}
                onCloseDirect={() => closeModal("save-load")}
                onSave1={() => openConfirmDialog("确认保存", "是否保存到槽位 1？", "save1")}
                onLoad1={() => openConfirmDialog("确认读取", "是否从槽位 1 读取存档？", "load1")}
                onSave2={() => openConfirmDialog("确认保存", "是否保存到槽位 2？", "save2")}
                onLoad2={() => openConfirmDialog("确认读取", "是否从槽位 2 读取存档？", "load2")}
                onSave3={() => openConfirmDialog("确认保存", "是否保存到槽位 3？", "save3")}
                onLoad3={() => openConfirmDialog("确认读取", "是否从槽位 3 读取存档？", "load3")}
              />
            ) : null}

            {isModalOpen("confirm") && confirmDialog ? (
              <ConfirmModal
                isTop={topModal === "confirm"}
                title={confirmDialog.title}
                message={confirmDialog.message}
                onCloseTop={closeConfirmDialog}
                onCancel={closeConfirmDialog}
                onConfirm={handleConfirmAction}
              />
            ) : null}
          </div>
        ) : null}

        {payload?.game_over ? (
          <GameOverModal
            payload={payload}
            onRestart={() =>
              openConfirmDialog("确认重开", "是否确认重新开始当前对局？", "restart")
            }
            onOpenSaveLoad={() => openModal("save-load")}
            onExportRecord={handleExportRecord}
            onBackToMenu={() => navigate("/")}
          />
        ) : null}
      </div>
    </div>
  );
}
