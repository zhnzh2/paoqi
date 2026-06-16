import { useState } from "react";
import type { GamePayload } from "../../types/game";

type UseGameActionRunnerParams = {
  onSuccessPayload: (payload: GamePayload) => void;
  onStatusMessage: (message: string) => void;
  onStatusIsError: (value: boolean) => void;
};

export default function useGameActionRunner({
  onSuccessPayload,
  onStatusMessage,
  onStatusIsError
}: UseGameActionRunnerParams) {
  const [busyScope, setBusyScope] = useState<"none" | "board" | "sidebar">("none");

  const isBoardBusy = busyScope === "board";
  const isSidebarBusy = busyScope === "sidebar";

  /**
   * 包装引擎调用（同步结果 → Promise）。
   * 引擎调用是同步的（<1ms），但保留 async 接口以便与现有调用方式兼容。
   * action() 返回 {ok, message, payload?} 或 {ok, message, data?} 结构。
   */
  async function runAction(
    action: () => any,
    scope: "board" | "sidebar" = "sidebar"
  ) {
    setBusyScope(scope);
    try {
      const res = action();
      if (res.ok) {
        onStatusMessage(res.message);
        onStatusIsError(false);
        if (res.payload) {
          onSuccessPayload(res.payload);
        } else if (res.data) {
          onSuccessPayload(res.data);
        }
      } else {
        onStatusMessage(res.message);
        onStatusIsError(true);
      }
    } catch (error) {
      onStatusMessage(`操作失败：${String(error)}`);
      onStatusIsError(true);
    } finally {
      setBusyScope("none");
    }
  }

  return {
    busyScope,
    isBoardBusy,
    isSidebarBusy,
    runAction
  };
}
