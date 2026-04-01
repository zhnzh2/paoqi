type SaveLoadModalProps = {
  isTop: boolean;
  onCloseTop: () => void;
  onCloseDirect: () => void;
  onSave1: () => void;
  onLoad1: () => void;
  onSave2: () => void;
  onLoad2: () => void;
  onSave3: () => void;
  onLoad3: () => void;
};

export default function SaveLoadModal({
  isTop,
  onCloseTop,
  onCloseDirect,
  onSave1,
  onLoad1,
  onSave2,
  onLoad2,
  onSave3,
  onLoad3
}: SaveLoadModalProps) {
  return (
    <div
      className={`modal-mask ${isTop ? "modal-mask-top" : "modal-mask-hidden"}`}
      onClick={() => {
        if (isTop) {
          onCloseTop();
        }
      }}
    >
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-title">存档管理</div>
        <div className="modal-message">
          请选择一个槽位进行保存或读取。
        </div>

        <div className="save-load-list">
          <div className="save-load-row">
            <div className="save-load-slot-label">槽位 1</div>
            <div className="save-load-row-actions">
              <button onClick={onSave1}>保存</button>
              <button onClick={onLoad1}>读取</button>
            </div>
          </div>

          <div className="save-load-row">
            <div className="save-load-slot-label">槽位 2</div>
            <div className="save-load-row-actions">
              <button onClick={onSave2}>保存</button>
              <button onClick={onLoad2}>读取</button>
            </div>
          </div>

          <div className="save-load-row">
            <div className="save-load-slot-label">槽位 3</div>
            <div className="save-load-row-actions">
              <button onClick={onSave3}>保存</button>
              <button onClick={onLoad3}>读取</button>
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button onClick={onCloseDirect}>关闭</button>
        </div>
      </div>
    </div>
  );
}