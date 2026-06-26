import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import UserBar from "../components/layout/UserBar";
import Board from "../components/board/Board";
import {
  getRecordDetail,
  type BoardCell,
  type RecordDetail,
  type RecordStep,
} from "../api/recordApi";

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

export default function RecordViewPage() {
  const { folderName } = useParams<{ folderName: string }>();
  const navigate = useNavigate();
  const [record, setRecord] = useState<RecordDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentStep, setCurrentStep] = useState(0); // 0 = 初始状态

  useEffect(() => {
    if (!folderName) {
      setError("对局记录地址无效");
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    getRecordDetail(folderName)
      .then((res) => {
        if (cancelled) return;
        if (res.ok && res.data) {
          setRecord(res.data);
          // 默认显示最后一步
          setCurrentStep(res.data.steps.length);
        } else {
          setError(res.message ?? "加载失败");
        }
      })
      .catch(() => {
        if (!cancelled) setError("网络错误");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [folderName]);

  const currentBoard = useMemo<BoardCell[][]>(() => {
    if (!record) return emptyBoard();
    if (currentStep === 0) return record.initial_board;
    return record.steps[currentStep - 1]?.board ?? record.initial_board;
  }, [record, currentStep]);

  const currentStepData: RecordStep | null =
    record && currentStep > 0 && record.steps[currentStep - 1]
      ? record.steps[currentStep - 1]
      : null;

  const info = record?.info;

  function stepColor(step: RecordStep): "R" | "B" {
    if (step.actor_color) return step.actor_color;
    return step.current_player === "R" ? "B" : "R";
  }

  if (loading) {
    return (
      <div className="page" style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#ccc" }}>
        加载中...
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="page" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh", color: "#f88", gap: 16 }}>
        <div>{error || "对局记录不存在"}</div>
        <button onClick={() => navigate("/")} style={{ padding: "8px 20px" }}>
          返回主页
        </button>
      </div>
    );
  }

  return (
    <div className="record-view-page">
      <UserBar />

      {/* 顶部信息栏 */}
      <div className="record-top-bar">
        <button className="record-back-btn" onClick={() => navigate(-1)}>
          ← 返回
        </button>
        <div className="record-top-info">
          <span className="record-top-title">对局回放</span>
          <span className="record-top-room">房间：{info?.room_code}</span>
        </div>
        <div className="record-top-result">
          {info?.winner ? (
            <span className={`record-top-winner record-top-winner-${info.winner}`}>
              {info.winner === "R" ? "红方胜" : "蓝方胜"}
            </span>
          ) : (
            <span className="record-top-winner">平局</span>
          )}
          <span className="record-top-endtype">
            {endTypeLabel(info?.end_type ?? "normal")}
          </span>
        </div>
      </div>

      {/* 对局双方信息 */}
      <div className="record-players-bar">
        <span className="record-player record-player-red">
          红方 {info?.red?.username ?? "?"}
        </span>
        <span className="record-vs">vs</span>
        <span className="record-player record-player-blue">
          蓝方 {info?.blue?.username ?? "?"}
        </span>
        <span className="record-meta-text">
          {info?.turn_number ?? 0} 回合 · {formatDuration(info?.duration_seconds ?? 0)}
        </span>
      </div>

      {/* 主体：棋盘 + 步列表 */}
      <div className="record-layout">
        {/* 左侧：棋盘 */}
        <div className="record-board-area">
          <h2 className="record-board-title">
            {currentStep === 0
              ? "初始局面"
              : `第 ${currentStep} 步：${currentStepData?.action_text ?? ""}`}
          </h2>
          <Board
            boardData={currentBoard}
            previewBoardData={null}
            highlightedCells={{}}
            hoveredCellKey={null}
            hoveredCannonCells={{}}
            arrowCells={{}}
            activePlayer={currentStepData?.current_player as "R" | "B" | null ?? null}
            showCoordText={false}
            isBusy={false}
            onCellClick={() => {}}
            onCellHover={() => {}}
            onCellLeave={() => {}}
          />

          {/* 步导航 */}
          <div className="record-step-nav">
            <button
              onClick={() => setCurrentStep(0)}
              disabled={currentStep === 0}
            >
              初始
            </button>
            <button
              onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
              disabled={currentStep === 0}
            >
              上一步
            </button>
            <span className="record-step-indicator">
              {currentStep} / {record.steps.length}
            </span>
            <button
              onClick={() =>
                setCurrentStep((s) => Math.min(record.steps.length, s + 1))
              }
              disabled={currentStep >= record.steps.length}
            >
              下一步
            </button>
            <button
              onClick={() => setCurrentStep(record.steps.length)}
              disabled={currentStep >= record.steps.length}
            >
              最终
            </button>
          </div>
        </div>

        {/* 右侧：步骤列表 */}
        <div className="record-steps-panel">
          <h3 className="record-steps-title">棋谱</h3>
          <div className="record-steps-list">
            <div
              className={`record-step-entry ${currentStep === 0 ? "record-step-active" : ""}`}
              role="button"
              tabIndex={0}
              onClick={() => setCurrentStep(0)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setCurrentStep(0);
                }
              }}
            >
              <span className="record-step-num">初始</span>
              <span className="record-step-text">初始局面</span>
            </div>
            {record.steps.map((step) => (
              <div
                key={step.step}
                className={`record-step-entry ${currentStep === step.step ? "record-step-active" : ""} record-step-${stepColor(step).toLowerCase()}`}
                role="button"
                tabIndex={0}
                onClick={() => setCurrentStep(step.step)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setCurrentStep(step.step);
                  }
                }}
              >
                <span className="record-step-num">
                  {step.step}.
                </span>
                <span className="record-step-color">
                  {stepColor(step) === "R" ? "红" : "蓝"}
                </span>
                <span className="record-step-text">
                  {step.action_text}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function emptyBoard(): BoardCell[][] {
  return Array.from({ length: 9 }, () => Array(9).fill(null));
}

function formatDuration(seconds: number): string {
  const rounded = Math.max(0, Math.round(seconds));
  if (rounded < 60) return `${rounded}秒`;
  return `${Math.floor(rounded / 60)}分${rounded % 60}秒`;
}
