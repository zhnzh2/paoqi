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

  async function runAction(
    action: () => Promise<any>,
    scope: "board" | "sidebar" = "sidebar"
  ) {
    setBusyScope(scope);
    try {
      const res = await action();
      if (res.ok) {
        onStatusMessage(res.message);
        onStatusIsError(false);
        if (res.data) {
          onSuccessPayload(res.data);
        }
      } else {
        onStatusMessage(res.message);
        onStatusIsError(true);
      }
    } catch (error) {
      onStatusMessage(`请求失败：${String(error)}`);
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