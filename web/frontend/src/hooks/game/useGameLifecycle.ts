import { useEffect } from "react";
import { getState, healthCheck } from "../../api/gameApi";
import type { GamePayload } from "../../types/game";

type UseGameLifecycleParams = {
  openLoadModalOnMount: boolean;
  payload: GamePayload | null;
  recordPage: number;
  totalRecordPages: number;
  onOpenModal: (name: string) => void;
  onHoveredCellClear: () => void;
  onInitLoadingChange: (value: boolean) => void;
  onBackendOkChange: (value: boolean) => void;
  onPayloadChange: (payload: GamePayload) => void;
  onStatusMessage: (message: string) => void;
  onStatusIsError: (value: boolean) => void;
  onRecordPageChange: (value: number) => void;
};

export default function useGameLifecycle({
  openLoadModalOnMount,
  payload,
  recordPage,
  totalRecordPages,
  onOpenModal,
  onHoveredCellClear,
  onInitLoadingChange,
  onBackendOkChange,
  onPayloadChange,
  onStatusMessage,
  onStatusIsError,
  onRecordPageChange
}: UseGameLifecycleParams) {
  useEffect(() => {
    if (openLoadModalOnMount) {
      onOpenModal("save-load");
    }
  }, [openLoadModalOnMount, onOpenModal]);

  useEffect(() => {
    if (payload?.game_over) {
      onHoveredCellClear();
    }
  }, [payload?.game_over, onHoveredCellClear]);

  useEffect(() => {
    async function init() {
      onInitLoadingChange(true);
      try {
        const health = await healthCheck();
        onBackendOkChange(health.ok);

        const state = await getState();
        if (state.ok) {
          onPayloadChange(state.data);
          onStatusMessage("已连接后端。");
          onStatusIsError(false);
        } else {
          onStatusMessage(state.message);
          onStatusIsError(true);
        }
      } catch (error) {
        onBackendOkChange(false);
        onStatusMessage(`初始化失败：${String(error)}`);
        onStatusIsError(true);
      } finally {
        onInitLoadingChange(false);
      }
    }

    init();
  }, [
    onInitLoadingChange,
    onBackendOkChange,
    onPayloadChange,
    onStatusMessage,
    onStatusIsError
  ]);

  useEffect(() => {
    if (recordPage > totalRecordPages) {
      onRecordPageChange(totalRecordPages);
    }
  }, [recordPage, totalRecordPages, onRecordPageChange]);
}