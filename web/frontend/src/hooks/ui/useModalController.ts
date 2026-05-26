import { useCallback, useState } from "react";

export type ConfirmActionType =
  | "save1"
  | "save2"
  | "save3"
  | "load1"
  | "load2"
  | "load3"
  | "restart"
  | "resign"
  | "endgame"
  | "confirm-pending";

export type ConfirmDialogState = {
  title: string;
  message: string;
  action: ConfirmActionType | null;
} | null;

export default function useModalController() {
  const [modalStack, setModalStack] = useState<string[]>([]);
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState>(null);

  const openModal = useCallback((name: string) => {
    setModalStack((prev) => {
      const next = prev.filter((item) => item !== name);
      next.push(name);
      return next;
    });
  }, []);

  const closeModal = useCallback((name: string) => {
    setModalStack((prev) => prev.filter((item) => item !== name));
  }, []);

  const closeTopModal = useCallback(() => {
    setModalStack((prev) => prev.slice(0, -1));
  }, []);

  const isModalOpen = useCallback(
    (name: string) => modalStack.includes(name),
    [modalStack]
  );

  const topModal = modalStack.length > 0 ? modalStack[modalStack.length - 1] : null;

  const openConfirmDialog = useCallback(
    (
      title: string,
      message: string,
      action: ConfirmActionType
    ) => {
      setConfirmDialog({ title, message, action });
      setModalStack((prev) => {
        const next = prev.filter((item) => item !== "confirm");
        next.push("confirm");
        return next;
      });
    },
    []
  );

  const closeConfirmDialog = useCallback(() => {
    setConfirmDialog(null);
    setModalStack((prev) => prev.filter((item) => item !== "confirm"));
  }, []);

  return {
    modalStack,
    confirmDialog,
    openModal,
    closeModal,
    closeTopModal,
    isModalOpen,
    topModal,
    openConfirmDialog,
    closeConfirmDialog
  };
}