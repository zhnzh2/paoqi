import { useEffect } from "react";

type UseModalEscapeCloseParams = {
  modalCount: number;
  topModal: string | null;
  onCloseTopModal: () => void;
  onCloseConfirmDialog: () => void;
};

export default function useModalEscapeClose({
  modalCount,
  topModal,
  onCloseTopModal,
  onCloseConfirmDialog
}: UseModalEscapeCloseParams) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && modalCount > 0) {
        if (topModal === "confirm") {
          onCloseConfirmDialog();
          return;
        }
        onCloseTopModal();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [modalCount, topModal, onCloseTopModal, onCloseConfirmDialog]);
}