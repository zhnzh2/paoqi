type ConfirmModalProps = {
  isTop: boolean;
  title: string;
  message: string;
  onCloseTop: () => void;
  onCancel: () => void;
  onConfirm: () => void;
};

export default function ConfirmModal({
  isTop,
  title,
  message,
  onCloseTop,
  onCancel,
  onConfirm
}: ConfirmModalProps) {
  return (
    <div
      className={`modal-mask ${isTop ? "modal-mask-top" : "modal-mask-hidden"}`}
      onClick={() => {
        if (isTop) {
          onCloseTop();
        }
      }}
    >
      <div className="modal-card modal-card-danger" onClick={(e) => e.stopPropagation()}>
        <div className="modal-title">{title}</div>
        <div className="modal-message">{message}</div>

        <div className="modal-actions">
          <button onClick={onCancel}>取消</button>
          <button
            className="danger-button"
            onClick={onConfirm}
          >
            确认
          </button>
        </div>
      </div>
    </div>
  );
}