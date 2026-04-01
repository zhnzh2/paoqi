type SettingsModalProps = {
  isTop: boolean;
  showRecordPanel: boolean;
  showCoordInsideCell: boolean;
  compactSidebar: boolean;
  showDropHighlight: boolean;
  showEatHighlight: boolean;
  showMuzzleHighlight: boolean;
  showFireHighlight: boolean;
  showArrowHints: boolean;
  showHoverPreview: boolean;
  showCannonHoverEnhance: boolean;
  onCloseTop: () => void;
  onCloseDirect: () => void;
  onChangeShowRecordPanel: (value: boolean) => void;
  onChangeShowCoordInsideCell: (value: boolean) => void;
  onChangeCompactSidebar: (value: boolean) => void;
  onChangeShowDropHighlight: (value: boolean) => void;
  onChangeShowEatHighlight: (value: boolean) => void;
  onChangeShowMuzzleHighlight: (value: boolean) => void;
  onChangeShowFireHighlight: (value: boolean) => void;
  onChangeShowArrowHints: (value: boolean) => void;
  onChangeShowHoverPreview: (value: boolean) => void;
  onChangeShowCannonHoverEnhance: (value: boolean) => void;
};

export default function SettingsModal({
  isTop,
  showRecordPanel,
  showCoordInsideCell,
  compactSidebar,
  showDropHighlight,
  showEatHighlight,
  showMuzzleHighlight,
  showFireHighlight,
  showArrowHints,
  showHoverPreview,
  showCannonHoverEnhance,
  onCloseTop,
  onCloseDirect,
  onChangeShowRecordPanel,
  onChangeShowCoordInsideCell,
  onChangeCompactSidebar,
  onChangeShowDropHighlight,
  onChangeShowEatHighlight,
  onChangeShowMuzzleHighlight,
  onChangeShowFireHighlight,
  onChangeShowArrowHints,
  onChangeShowHoverPreview,
  onChangeShowCannonHoverEnhance
}: SettingsModalProps) {
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
        <div className="modal-title">设置</div>

        <div className="settings-group">
          <div className="settings-group-title">界面显示</div>
          <div className="settings-list">
            <label className="settings-item">
              <input
                type="checkbox"
                checked={showRecordPanel}
                onChange={(e) => onChangeShowRecordPanel(e.target.checked)}
              />
              显示棋谱
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={showCoordInsideCell}
                onChange={(e) => onChangeShowCoordInsideCell(e.target.checked)}
              />
              格内显示坐标
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={compactSidebar}
                onChange={(e) => onChangeCompactSidebar(e.target.checked)}
              />
              右栏紧凑模式
            </label>
          </div>
        </div>

        <div className="settings-group">
          <div className="settings-group-title">高亮与提示</div>
          <div className="settings-list">
            <label className="settings-item">
              <input
                type="checkbox"
                checked={showDropHighlight}
                onChange={(e) => onChangeShowDropHighlight(e.target.checked)}
              />
              显示落子 hover 高亮
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={showEatHighlight}
                onChange={(e) => onChangeShowEatHighlight(e.target.checked)}
              />
              显示吃子高亮
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={showMuzzleHighlight}
                onChange={(e) => onChangeShowMuzzleHighlight(e.target.checked)}
              />
              显示炮口高亮
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={showFireHighlight}
                onChange={(e) => onChangeShowFireHighlight(e.target.checked)}
              />
              显示打炮高亮
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={showArrowHints}
                onChange={(e) => onChangeShowArrowHints(e.target.checked)}
              />
              显示炮口方向箭头
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={showHoverPreview}
                onChange={(e) => onChangeShowHoverPreview(e.target.checked)}
              />
              显示 hover 虚化预览
            </label>

            <label className="settings-item">
              <input
                type="checkbox"
                checked={showCannonHoverEnhance}
                onChange={(e) => onChangeShowCannonHoverEnhance(e.target.checked)}
              />
              显示炮管 hover 增强高亮
            </label>
          </div>
        </div>

        <div className="modal-actions">
          <button onClick={onCloseDirect}>关闭</button>
        </div>
      </div>
    </div>
  );
}