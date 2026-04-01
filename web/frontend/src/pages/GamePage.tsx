import { useEffect, useState } from "react";
import {
  confirmPending,
  endGameByAgreement,
  exportRecord,
  loadFromSlot,
  newGame,
  resignGame,
  restartGame,
  saveToSlot,
  undoAction
} from "../api/gameApi";
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

type GamePageProps = {
  onBackToMenu: () => void;
  openLoadModalOnMount?: boolean;
};

export default function GamePage({ onBackToMenu, openLoadModalOnMount = false }: GamePageProps) {
  const [backendOk, setBackendOk] = useState<boolean>(false);
  const [initLoading, setInitLoading] = useState<boolean>(false);
  const [payload, setPayload] = useState<GamePayload | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("正在连接后端...");
  const [statusIsError, setStatusIsError] = useState<boolean>(false);
  const [hoveredCell, setHoveredCell] = useState<{ x: number; y: number } | null>(null);
  const [recordPage, setRecordPage] = useState<number>(1);
  const recordPageSize = 20;

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
    onSuccessPayload: setPayload,
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
    onRunAction: runAction,
    onStatusMessage: setStatusMessage,
    onStatusIsError: setStatusIsError,
    onHoveredCellChange: setHoveredCell
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
    onInitLoadingChange: setInitLoading,
    onBackendOkChange: setBackendOk,
    onPayloadChange: setPayload,
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

  return (
    <div className="page">
      <div className="layout">
        <GameBoardSection
          boardData={boardData}
          previewBoardData={previewBoardData ?? boardData}
          highlightedCells={highlightedCells}
          hoveredCellKey={hoveredCellKey}
          hoveredCannonCells={hoveredCannonCells}
          arrowCells={arrowCells}
          activePlayer={payload?.current_player ?? null}
          showCoordText={showCoordInsideCell}
          isBusy={isBoardBusy || modalStack.length > 0 || Boolean(payload?.game_over)}
          dangerDisabled={initLoading || isSidebarBusy}
          onCellClick={handleBoardCellClick}
          onCellHover={handleBoardCellHover}
          onCellLeave={handleBoardCellLeave}
          onEndgame={() =>
            openConfirmDialog(
              "确认终局",
              "是否确认双方同意结束当前对局？\n系统将按当前局面计算胜负。",
              "endgame"
            )
          }
          onResign={() =>
            openConfirmDialog(
              "确认投降",
              "是否确认当前行动方投降？\n确认后将直接判负。",
              "resign"
            )
          }
          onBackToMenu={onBackToMenu}
        />

        <GameSidebar
          compactSidebar={compactSidebar}
          backendOk={backendOk}
          initLoading={initLoading}
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
          onNewGame={() => runAction(newGame, "sidebar")}
          onRestart={() =>
            openConfirmDialog("确认重开", "是否确认重新开始当前对局？", "restart")
          }
          onUndo={() => runAction(undoAction, "sidebar")}
          onExportRecord={() => runAction(exportRecord, "sidebar")}
          onOpenSaveLoad={() => openModal("save-load")}
          onOpenSettings={() => openModal("settings")}
          onConfirmPending={() =>
            openConfirmDialog(
              "确认自动动作",
              "是否确认执行当前待确认自动动作？",
              "confirm-pending"
            )
          }
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
                onSave1={() =>
                  openConfirmDialog("确认保存", "是否保存到槽位 1？", "save1")
                }
                onLoad1={() =>
                  openConfirmDialog("确认读取", "是否从槽位 1 读取存档？", "load1")
                }
                onSave2={() =>
                  openConfirmDialog("确认保存", "是否保存到槽位 2？", "save2")
                }
                onLoad2={() =>
                  openConfirmDialog("确认读取", "是否从槽位 2 读取存档？", "load2")
                }
                onSave3={() =>
                  openConfirmDialog("确认保存", "是否保存到槽位 3？", "save3")
                }
                onLoad3={() =>
                  openConfirmDialog("确认读取", "是否从槽位 3 读取存档？", "load3")
                }
              />
            ) : null}

            {isModalOpen("confirm") && confirmDialog ? (
              <ConfirmModal
                isTop={topModal === "confirm"}
                title={confirmDialog.title}
                message={confirmDialog.message}
                onCloseTop={closeConfirmDialog}
                onCancel={closeConfirmDialog}
                onConfirm={async () => {
                  const action = confirmDialog.action;
                  closeConfirmDialog();

                  if (action === "save1") {
                    await runAction(() => saveToSlot(1), "sidebar");
                    return;
                  }
                  if (action === "save2") {
                    await runAction(() => saveToSlot(2), "sidebar");
                    return;
                  }
                  if (action === "save3") {
                    await runAction(() => saveToSlot(3), "sidebar");
                    return;
                  }

                  if (action === "load1") {
                    await runAction(() => loadFromSlot(1), "sidebar");
                    return;
                  }
                  if (action === "load2") {
                    await runAction(() => loadFromSlot(2), "sidebar");
                    return;
                  }
                  if (action === "load3") {
                    await runAction(() => loadFromSlot(3), "sidebar");
                    return;
                  }

                  if (action === "restart") {
                    await runAction(restartGame, "sidebar");
                    return;
                  }

                  if (action === "confirm-pending") {
                    await runAction(confirmPending, "sidebar");
                    return;
                  }

                  if (action === "endgame") {
                    await runAction(endGameByAgreement, "sidebar");
                    return;
                  }

                  if (action === "resign") {
                    await runAction(resignGame, "sidebar");
                    return;
                  }
                }}
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
            onExportRecord={() => runAction(exportRecord, "sidebar")}
            onBackToMenu={onBackToMenu}
          />
        ) : null}
      </div>
    </div>
  );
}