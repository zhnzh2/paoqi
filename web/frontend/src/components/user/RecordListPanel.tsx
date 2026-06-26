import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  downloadAllRecords,
  downloadRecord,
  getUserRecords,
  type RecordSummary,
} from "../../api/recordApi";

type RecordListPanelProps = {
  uid: number;
};

function endTypeLabel(t: string): string {
  switch (t) {
    case "resign":
      return "投降";
    case "agreement":
      return "协商终局";
    default:
      return "自然终局";
  }
}

function formatDuration(seconds: number): string {
  seconds = Math.max(0, Math.round(seconds));
  if (seconds < 60) return `${seconds}秒`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}分${s}秒`;
}

function formatTime(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function RecordListPanel({ uid }: RecordListPanelProps) {
  const navigate = useNavigate();
  const [records, setRecords] = useState<RecordSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getUserRecords(uid)
      .then((res) => {
        if (cancelled) return;
        if (res.ok && res.data?.records) {
          setRecords(res.data.records);
        } else {
          setLoadError(res.message ?? "加载失败");
        }
      })
      .catch(() => {
        if (!cancelled) setLoadError("网络错误");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [uid]);

  if (loading) return <div className="user-content-loading">加载中...</div>;
  if (loadError) {
    return <div className="user-content-error">{loadError}</div>;
  }

  if (records.length === 0) {
    return (
      <div className="user-panel">
        <h2 className="user-panel-title">历史对局</h2>
        <p className="user-panel-desc">暂无已完成的对局记录</p>
      </div>
    );
  }

  const handleDownload = async (
    key: string,
    download: () => Promise<void>,
  ) => {
    setDownloading(key);
    setDownloadError("");
    try {
      await download();
    } catch (caughtError) {
      setDownloadError(
        caughtError instanceof Error ? caughtError.message : "下载失败",
      );
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="user-panel">
      <h2 className="user-panel-title">历史对局</h2>
      <p className="user-panel-desc">
        共 {records.length} 场对局
        <button
          type="button"
          className="record-download-all-btn"
          disabled={downloading !== null}
          onClick={() =>
            handleDownload("all", () => downloadAllRecords(uid))
          }
        >
          {downloading === "all" ? "正在打包..." : "下载全部"}
        </button>
      </p>
      {downloadError ? (
        <div className="user-content-error">{downloadError}</div>
      ) : null}

      <div className="record-list">
        {records.map((r) => {
          const isRed = r.red?.uid === uid;
          const mySide = isRed ? "红方" : "蓝方";
          const opponent = isRed ? r.blue?.username : r.red?.username;
          const won =
            (isRed && r.winner === "R") || (!isRed && r.winner === "B");
          const lost =
            (isRed && r.winner === "B") || (!isRed && r.winner === "R");

          return (
            <div
              key={r.folder_name}
              className="record-list-item"
              role="button"
              tabIndex={0}
              onClick={() =>
                navigate(`/record/${encodeURIComponent(r.folder_name)}`)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  navigate(`/record/${encodeURIComponent(r.folder_name)}`);
                }
              }}
            >
              <div className="record-item-left">
                <span
                  className={`record-item-result ${won ? "record-item-won" : lost ? "record-item-lost" : "record-item-draw"}`}
                >
                  {won ? "胜" : lost ? "负" : "平"}
                </span>
                <span className="record-item-sides">
                  {mySide} vs {opponent ?? "?"}
                </span>
              </div>
              <div className="record-item-right">
                <span className="record-item-endtype">
                  {endTypeLabel(r.end_type)}
                </span>
                <span className="record-item-meta">
                  {r.turn_number} 回合 · {formatDuration(r.duration_seconds)}
                </span>
                <span className="record-item-time">
                  {formatTime(r.created_at)}
                </span>
                <button
                  type="button"
                  className="record-item-download"
                  title="下载此对局"
                  disabled={downloading !== null}
                  onClick={(event) => {
                    event.stopPropagation();
                    void handleDownload(r.folder_name, () =>
                      downloadRecord(r.folder_name),
                    );
                  }}
                >
                  {downloading === r.folder_name ? "下载中" : "下载"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
