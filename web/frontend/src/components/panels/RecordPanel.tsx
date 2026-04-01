type RecordPanelProps = {
  recordCollapsed: boolean;
  recordPage: number;
  totalRecordPages: number;
  pagedHistory: string[];
  recordPageSize: number;
  onToggleCollapsed: () => void;
  onPrevPage: () => void;
  onNextPage: () => void;
};

export default function RecordPanel({
  recordCollapsed,
  recordPage,
  totalRecordPages,
  pagedHistory,
  recordPageSize,
  onToggleCollapsed,
  onPrevPage,
  onNextPage
}: RecordPanelProps) {
  return (
    <div className="section">
      <div className="record-header">
        <h2>棋谱</h2>
        <div className="record-header-actions">
          <button
            type="button"
            onClick={onToggleCollapsed}
          >
            {recordCollapsed ? "展开" : "折叠"}
          </button>
        </div>
      </div>

      {!recordCollapsed ? (
        <>
          <div className="record-panel">
            {pagedHistory.length > 0 ? (
              pagedHistory.map((line, index) => {
                const absoluteIndex = (recordPage - 1) * recordPageSize + index + 1;
                return (
                  <div key={`${absoluteIndex}-${line}`} className="record-line">
                    <span className="record-index">{absoluteIndex}.</span>
                    <span className="record-text">{line}</span>
                  </div>
                );
              })
            ) : (
              <div className="record-empty">暂无棋谱</div>
            )}
          </div>

          <div className="record-pagination">
            <button
              type="button"
              onClick={onPrevPage}
              disabled={recordPage <= 1}
            >
              上一页
            </button>

            <span className="record-pagination-text">
              第 {recordPage} / {totalRecordPages} 页
            </span>

            <button
              type="button"
              onClick={onNextPage}
              disabled={recordPage >= totalRecordPages}
            >
              下一页
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}