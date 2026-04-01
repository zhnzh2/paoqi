import { useCallback, useEffect, useMemo, useState } from "react";
import {
  applyAction,
  confirmPending,
  endGameByAgreement,
  exportRecord,
  getState,
  healthCheck,
  loadFromSlot,
  newGame,
  resignGame,
  restartGame,
  saveToSlot,
  undoAction
} from "../api/gameApi";
import Board from "../components/Board";
import type { GameAction, GamePayload } from "../types/game";

export default function GamePage() {
  type HighlightType = "drop" | "eat" | "muzzle" | "fire" | null;
  function normalizeCannonPositions(cannon: any): Array<{ x: number; y: number }> {
    if (!cannon) {
      return [];
    }

    if (Array.isArray(cannon.cells)) {
      return cannon.cells
        .map((cell: any) => {
          if (cell && typeof cell.x === "number" && typeof cell.y === "number") {
            return { x: cell.x, y: cell.y };
          }

          if (Array.isArray(cell) && cell.length >= 2) {
            return { x: Number(cell[0]), y: Number(cell[1]) };
          }

          return null;
        })
        .filter((cell: any) => cell !== null);
    }

    if (Array.isArray(cannon.positions)) {
      return cannon.positions
        .map((pos: any) => {
          if (pos && typeof pos.x === "number" && typeof pos.y === "number") {
            return { x: pos.x, y: pos.y };
          }

          if (Array.isArray(pos) && pos.length >= 2) {
            return { x: Number(pos[0]), y: Number(pos[1]) };
          }

          return null;
        })
        .filter((pos: any) => pos !== null);
    }

    return [];
  }

  function isCannonEndpoint(cannon: any, x: number, y: number): boolean {
    const positions = normalizeCannonPositions(cannon);
    if (positions.length === 0) {
      return false;
    }

    const first = positions[0];
    const last = positions[positions.length - 1];

    const hitFirst = first.x === x && first.y === y;
    const hitLast = last.x === x && last.y === y;
    return hitFirst || hitLast;
  }

  function isInsideCannon(cannon: any, x: number, y: number): boolean {
    const positions = normalizeCannonPositions(cannon);
    return positions.some((pos) => pos.x === x && pos.y === y);
  }

  function matchMuzzleActionByEndpoint(action: GameAction, x: number, y: number): boolean {
    if (action.type !== "muzzle") {
      return false;
    }

    const positions = normalizeCannonPositions(action.cannon);
    if (positions.length === 0) {
      return false;
    }

    const xs = positions.map((pos) => pos.x);
    const ys = positions.map((pos) => pos.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    if (action.direction === "left") {
      return x === minX && y >= minY && y <= maxY;
    }

    if (action.direction === "right") {
      return x === maxX && y >= minY && y <= maxY;
    }

    if (action.direction === "up") {
      return y === minY && x >= minX && x <= maxX;
    }

    if (action.direction === "down") {
      return y === maxY && x >= minX && x <= maxX;
    }

    return false;
  }

  function getMuzzleEndpointDirection(action: GameAction): { x: number; y: number } | null {
    if (action.type !== "muzzle") {
      return null;
    }

    const positions = normalizeCannonPositions(action.cannon);
    if (positions.length === 0) {
      return null;
    }

    const xs = positions.map((pos) => pos.x);
    const ys = positions.map((pos) => pos.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    if (action.direction === "left") {
      const pos = positions.find((p) => p.x === minX);
      return pos ?? null;
    }

    if (action.direction === "right") {
      const pos = positions.find((p) => p.x === maxX);
      return pos ?? null;
    }

    if (action.direction === "up") {
      const pos = positions.find((p) => p.y === minY);
      return pos ?? null;
    }

    if (action.direction === "down") {
      const pos = positions.find((p) => p.y === maxY);
      return pos ?? null;
    }

    return null;
  }

  function buildHighlightedCells(payload: GamePayload | null): Record<string, HighlightType> {
    const result: Record<string, HighlightType> = {};

    if (!payload) {
      return result;
    }

    const phase = payload.phase;
    const actions = payload.legal_actions ?? [];

    if (phase === "drop" && showDropHighlight) {
      for (const action of actions) {
        if (action.type === "move" && typeof action.x === "number" && typeof action.y === "number") {
          result[`${action.x},${action.y}`] = "drop";
        }
      }
      return result;
    }

    if (phase === "eat" && showEatHighlight) {
      for (const action of actions) {
        if (action.type === "eat" && typeof action.x === "number" && typeof action.y === "number") {
          result[`${action.x},${action.y}`] = "eat";
        }
      }
      return result;
    }

    if (phase === "muzzle" && showMuzzleHighlight) {
      for (const action of actions) {
        const endpoint = getMuzzleEndpointDirection(action);
        if (endpoint) {
          result[`${endpoint.x},${endpoint.y}`] = "muzzle";
        }
      }
      return result;
    }

    if (phase === "fire" && showFireHighlight) {
      for (const action of actions) {
        if (action.type !== "fire") {
          continue;
        }

        const positions = normalizeCannonPositions(action.cannon);
        for (const pos of positions) {
          result[`${pos.x},${pos.y}`] = "fire";
        }
      }
      return result;
    }

    return result;
  }

  function buildEmptyBoard(): ({ color: "R" | "B"; level: number } | null)[][] {
    return Array.from({ length: 9 }, () => Array.from({ length: 9 }, () => null));
  }

  function cloneBoardData(board: ({ color: "R" | "B"; level: number } | null)[][]) {
    return board.map((row) =>
      row.map((cell) => {
        if (!cell) {
          return null;
        }
        return { ...cell };
      })
    );
  }

  function buildPreviewBoard(
    payload: GamePayload | null,
    hovered: { x: number; y: number } | null
  ): ({ color: "R" | "B"; level: number } | null)[][] | null {
    if (!payload || !hovered) {
      return null;
    }

    if (payload.has_pending_auto_action) {
      return null;
    }

    const baseBoard = payload.snapshot?.board;
    if (!baseBoard) {
      return null;
    }

    const action = findActionByCell(payload.legal_actions, payload.phase, hovered.x, hovered.y);
    if (!action) {
      return null;
    }

    const board = cloneBoardData(baseBoard);

    if (payload.phase === "drop" && action.type === "move") {
      const row = hovered.y - 1;
      const col = hovered.x - 1;
      const existing = board[row][col];

      if (!existing) {
        board[row][col] = {
          color: payload.current_player,
          level: 1
        };
      } else if (existing.color === payload.current_player) {
        board[row][col] = {
          color: existing.color,
          level: existing.level + 1
        };
      }

      return board;
    }

    if (payload.phase === "eat" && action.type === "eat") {
      const row = hovered.y - 1;
      const col = hovered.x - 1;
      board[row][col] = {
        color: payload.current_player,
        level: 1
      };
      return board;
    }

    return null;
  }

  function buildHoveredCannonCells(
    payload: GamePayload | null,
    hovered: { x: number; y: number } | null
  ): Record<string, true> {
    const result: Record<string, true> = {};

    if (!payload || !hovered) {
      return result;
    }

    const actions = payload.legal_actions ?? [];
    const phase = payload.phase;

    if (phase !== "muzzle" && phase !== "fire") {
      return result;
    }

    for (const action of actions) {
      if (phase === "muzzle" && action.type !== "muzzle") {
        continue;
      }
      if (phase === "fire" && action.type !== "fire") {
        continue;
      }

      const positions = normalizeCannonPositions(action.cannon);
      const containsHovered = positions.some(
        (pos) => pos.x === hovered.x && pos.y === hovered.y
      );

      if (!containsHovered) {
        continue;
      }

      for (const pos of positions) {
        result[`${pos.x},${pos.y}`] = true;
      }
      return result;
    }

    return result;
  }

  function findActionByCell(actions: GameAction[], phase: string, x: number, y: number): GameAction | null {
    if (phase === "drop") {
      return (
        actions.find((action) => {
          return action.type === "move" && action.x === x && action.y === y;
        }) ?? null
      );
    }

    if (phase === "eat") {
      return (
        actions.find((action) => {
          return action.type === "eat" && action.x === x && action.y === y;
        }) ?? null
      );
    }

    if (phase === "muzzle") {
      const matched = actions.filter((action) => {
        return matchMuzzleActionByEndpoint(action, x, y);
      });

      if (matched.length === 1) {
        return matched[0];
      }

      return null;
    }

    if (phase === "fire") {
      const matched = actions.filter((action) => {
        return action.type === "fire" && isInsideCannon(action.cannon, x, y);
      });

      if (matched.length === 1) {
        return matched[0];
      }

      return null;
    }

    return null;
  }

  async function handleBoardCellClick(x: number, y: number) {
    if (!payload || loading || modalStack.length > 0 || payload.game_over) {
      return;
    }

    const action = findActionByCell(payload.legal_actions, payload.phase, x, y);
    if (!action) {
      setStatusMessage(`(${x}, ${y}) 不是当前阶段可执行的位置，或该位置对应多个候选动作。`);
      setStatusIsError(true);
      return;
    }

    setStatusMessage(`正在处理 (${x}, ${y}) 的点击...`);
    setStatusIsError(false);

    await runAction(() => applyAction(action));
    setHoveredCell(null);
  }
  function handleBoardCellHover(x: number, y: number) {
    if (loading || modalStack.length > 0 || payload?.game_over) {
      return;
    }
    setHoveredCell({ x, y });
  }

  function handleBoardCellLeave() {
    setHoveredCell(null);
  }
  const [backendOk, setBackendOk] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [payload, setPayload] = useState<GamePayload | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("正在连接后端...");
  const [statusIsError, setStatusIsError] = useState<boolean>(false);
  const [hoveredCell, setHoveredCell] = useState<{ x: number; y: number } | null>(null);
  const [previewBoardData, setPreviewBoardData] = useState<({ color: "R" | "B"; level: number } | null)[][] | null>(null);
  const [showRecordPanel, setShowRecordPanel] = useState<boolean>(true);
  const [showCoordInsideCell, setShowCoordInsideCell] = useState<boolean>(false);
  const [showDropHighlight, setShowDropHighlight] = useState<boolean>(true);
  const [showEatHighlight, setShowEatHighlight] = useState<boolean>(true);
  const [showMuzzleHighlight, setShowMuzzleHighlight] = useState<boolean>(true);
  const [showFireHighlight, setShowFireHighlight] = useState<boolean>(true);

  const [modalStack, setModalStack] = useState<string[]>([]);

  const [confirmDialog, setConfirmDialog] = useState<{
    title: string;
    message: string;
    action:
      | "save1"
      | "save2"
      | "save3"
      | "load1"
      | "load2"
      | "load3"
      | "restart"
      | "resign"
      | "endgame"
      | "confirm-pending"
      | null;
  } | null>(null);

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
      action:
        | "save1"
        | "save2"
        | "save3"
        | "load1"
        | "load2"
        | "load3"
        | "restart"
        | "resign"
        | "endgame"
        | "confirm-pending"
    ) => {
      setConfirmDialog({ title, message, action });
      openModal("confirm");
    },
    [openModal]
  );

  const closeConfirmDialog = useCallback(() => {
    setConfirmDialog(null);
    closeModal("confirm");
  }, [closeModal]);

  async function runAction(action: () => Promise<any>) {
    setLoading(true);
    try {
      const res = await action();
      if (res.ok) {
        setStatusMessage(res.message);
        setStatusIsError(false);
        if (res.data) {
          setPayload(res.data);
        }
      } else {
        setStatusMessage(res.message);
        setStatusIsError(true);
      }
    } catch (error) {
      setStatusMessage(`请求失败：${String(error)}`);
      setStatusIsError(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    async function init() {
      setLoading(true);
      try {
        const health = await healthCheck();
        setBackendOk(health.ok);

        const state = await getState();
        if (state.ok) {
          setPayload(state.data);
          setStatusMessage("已连接后端。");
          setStatusIsError(false);
        } else {
          setStatusMessage(state.message);
          setStatusIsError(true);
        }
      } catch (error) {
        setBackendOk(false);
        setStatusMessage(`初始化失败：${String(error)}`);
        setStatusIsError(true);
      } finally {
        setLoading(false);
      }
    }

    init();
  }, []);

  useEffect(() => {
    const preview = buildPreviewBoard(payload, hoveredCell);
    setPreviewBoardData(preview);
  }, [payload, hoveredCell]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && modalStack.length > 0) {
        if (topModal === "confirm") {
          closeConfirmDialog();
          return;
        }
        closeTopModal();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [modalStack, topModal, closeTopModal, closeConfirmDialog]);

  const boardData = useMemo(() => {
    if (!payload?.snapshot?.board) {
      return buildEmptyBoard();
    }
    return payload.snapshot.board;
  }, [payload]);

  const highlightedCells = useMemo(() => {
    return buildHighlightedCells(payload);
  }, [payload]);

  const hoveredCellKey = useMemo(() => {
    if (!hoveredCell) {
      return null;
    }
    return `${hoveredCell.x},${hoveredCell.y}`;
  }, [hoveredCell]);

  const hoveredCannonCells = useMemo(() => {
    return buildHoveredCannonCells(payload, hoveredCell);
  }, [payload, hoveredCell]);

  const pendingAutoMessage = useMemo(() => {
    if (!payload) {
      return "";
    }

    if (!payload.has_pending_auto_action) {
      return "";
    }

    if (Array.isArray(payload.auto_action_messages) && payload.auto_action_messages.length > 0) {
      return payload.auto_action_messages[payload.auto_action_messages.length - 1];
    }

    return "当前存在待确认自动动作，请点击“确认自动动作”。";
  }, [payload]);

  return (
    <div className="page">
      <div className="layout">
        <div className="left-column">
          <h1>炮棋 Web 原型</h1>
          <Board
            boardData={boardData}
            previewBoardData={previewBoardData ?? boardData}
            highlightedCells={highlightedCells}
            hoveredCellKey={hoveredCellKey}
            hoveredCannonCells={hoveredCannonCells}
            showCoordText={showCoordInsideCell}
            isBusy={loading || modalStack.length > 0}
            onCellClick={handleBoardCellClick}
            onCellHover={handleBoardCellHover}
            onCellLeave={handleBoardCellLeave}
          />
        </div>

        <div className="right-column">
          <div className="panel">
            <div className="section">
              <div><strong>后端状态：</strong>{backendOk ? "已连接" : "未连接"}</div>
              <div>
                <strong>当前提示：</strong>
                <span className={statusIsError ? "error" : "ok"}>{statusMessage}</span>
              </div>
              <div><strong>加载中：</strong>{loading ? "是" : "否"}</div>
            </div>

            <div className="section button-grid">
              <button onClick={() => runAction(newGame)} disabled={loading}>开始新对局</button>
              <button
                onClick={() =>
                  openConfirmDialog("确认重开", "是否确认重新开始当前对局？", "restart")
                }
                disabled={loading}
              >
                重开
              </button>
              <button onClick={() => runAction(undoAction)} disabled={loading}>撤销</button>
              <button onClick={() => runAction(exportRecord)} disabled={loading}>导出棋谱</button>
              <button onClick={() => openModal("save-load")} disabled={loading}>存档</button>
              <button onClick={() => openModal("settings")} disabled={loading}>设置</button>
            </div>

            <div className="section">
              <h2>当前局面信息</h2>
              {payload ? (
                <div className="info-grid">
                  <div><strong>当前玩家：</strong>{payload.current_player}</div>
                  <div><strong>当前阶段：</strong>{payload.phase}</div>
                  <div><strong>回合数：</strong>{payload.turn_number}</div>
                  <div><strong>游戏结束：</strong>{payload.game_over ? "是" : "否"}</div>
                  <div><strong>胜方：</strong>{payload.winner ?? "无"}</div>
                  <div><strong>合法动作数：</strong>{payload.legal_actions.length}</div>
                  <div><strong>有待确认自动动作：</strong>{payload.has_pending_auto_action ? "是" : "否"}</div>
                  <div><strong>棋谱条目数：</strong>{payload.history.length}</div>
                </div>
              ) : (
                <div>暂无数据</div>
              )}
            </div>

            {payload?.has_pending_auto_action ? (
              <div className="section">
                <div className="pending-auto-box">
                  <div className="pending-auto-title">待确认自动动作</div>
                  <div className="pending-auto-text">{pendingAutoMessage}</div>
                  <button
                    onClick={() =>
                      openConfirmDialog(
                        "确认自动动作",
                        "是否确认执行当前待确认自动动作？",
                        "confirm-pending"
                      )
                    }
                    disabled={loading}
                    className="pending-auto-button"
                  >
                    确认自动动作
                  </button>
                </div>
              </div>
            ) : null}

            {showRecordPanel ? (
              <div className="section">
                <h2>棋谱</h2>
                <div className="record-panel">
                  {payload && payload.history.length > 0 ? (
                    payload.history.map((line, index) => (
                      <div key={`${index}-${line}`} className="record-line">
                        <span className="record-index">{index + 1}.</span>
                        <span className="record-text">{line}</span>
                      </div>
                    ))
                  ) : (
                    <div className="record-empty">暂无棋谱</div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
        {modalStack.length > 0 ? (
          <div className="modal-overlay-root">
            {isModalOpen("settings") ? (
              <div
                className={`modal-mask ${topModal === "settings" ? "modal-mask-top" : "modal-mask-hidden"}`}
                onClick={() => {
                  if (topModal === "settings") {
                    closeTopModal();
                  }
                }}
              >
                <div className="modal-card" onClick={(e) => e.stopPropagation()}>
                  <div className="modal-title">设置</div>

                  <div className="settings-list">
                    <label className="settings-item">
                      <input
                        type="checkbox"
                        checked={showRecordPanel}
                        onChange={(e) => setShowRecordPanel(e.target.checked)}
                      />
                      显示棋谱
                    </label>

                    <label className="settings-item">
                      <input
                        type="checkbox"
                        checked={showCoordInsideCell}
                        onChange={(e) => setShowCoordInsideCell(e.target.checked)}
                      />
                      格内显示坐标
                    </label>

                    <label className="settings-item">
                      <input
                        type="checkbox"
                        checked={showDropHighlight}
                        onChange={(e) => setShowDropHighlight(e.target.checked)}
                      />
                      显示落子高亮
                    </label>

                    <label className="settings-item">
                      <input
                        type="checkbox"
                        checked={showEatHighlight}
                        onChange={(e) => setShowEatHighlight(e.target.checked)}
                      />
                      显示吃子高亮
                    </label>

                    <label className="settings-item">
                      <input
                        type="checkbox"
                        checked={showMuzzleHighlight}
                        onChange={(e) => setShowMuzzleHighlight(e.target.checked)}
                      />
                      显示炮口高亮
                    </label>

                    <label className="settings-item">
                      <input
                        type="checkbox"
                        checked={showFireHighlight}
                        onChange={(e) => setShowFireHighlight(e.target.checked)}
                      />
                      显示打炮高亮
                    </label>
                  </div>

                  <div className="settings-danger-group">
                    <button
                      className="danger-button"
                      onClick={() =>
                        openConfirmDialog(
                          "确认终局",
                          "是否确认双方同意结束当前对局？\n系统将按当前局面计算胜负。",
                          "endgame"
                        )
                      }
                    >
                      协商终局
                    </button>

                    <button
                      className="danger-button"
                      onClick={() =>
                        openConfirmDialog(
                          "确认投降",
                          "是否确认当前行动方投降？\n确认后将直接判负。",
                          "resign"
                        )
                      }
                    >
                      投降
                    </button>
                  </div>

                  <div className="modal-actions">
                    <button onClick={() => closeModal("settings")}>关闭</button>
                  </div>
                </div>
              </div>
            ) : null}

            {isModalOpen("save-load") ? (
              <div
                className={`modal-mask ${topModal === "save-load" ? "modal-mask-top" : "modal-mask-hidden"}`}
                onClick={() => {
                  if (topModal === "save-load") {
                    closeTopModal();
                  }
                }}
              >
                <div className="modal-card" onClick={(e) => e.stopPropagation()}>
                  <div className="modal-title">存档</div>

                  <div className="save-load-grid">
                    <button
                      onClick={() =>
                        openConfirmDialog("确认保存", "是否保存到槽位 1？", "save1")
                      }
                    >
                      保存到槽位 1
                    </button>
                    <button
                      onClick={() =>
                        openConfirmDialog("确认读取", "是否从槽位 1 读取存档？", "load1")
                      }
                    >
                      从槽位 1 读取
                    </button>

                    <button
                      onClick={() =>
                        openConfirmDialog("确认保存", "是否保存到槽位 2？", "save2")
                      }
                    >
                      保存到槽位 2
                    </button>
                    <button
                      onClick={() =>
                        openConfirmDialog("确认读取", "是否从槽位 2 读取存档？", "load2")
                      }
                    >
                      从槽位 2 读取
                    </button>

                    <button
                      onClick={() =>
                        openConfirmDialog("确认保存", "是否保存到槽位 3？", "save3")
                      }
                    >
                      保存到槽位 3
                    </button>
                    <button
                      onClick={() =>
                        openConfirmDialog("确认读取", "是否从槽位 3 读取存档？", "load3")
                      }
                    >
                      从槽位 3 读取
                    </button>
                  </div>

                  <div className="modal-actions">
                    <button onClick={() => closeModal("save-load")}>关闭</button>
                  </div>
                </div>
              </div>
            ) : null}

            {isModalOpen("confirm") && confirmDialog ? (
              <div
                className={`modal-mask ${topModal === "confirm" ? "modal-mask-top" : "modal-mask-hidden"}`}
                onClick={() => {
                  if (topModal === "confirm") {
                    closeConfirmDialog();
                  }
                }}
              >
                <div className="modal-card modal-card-danger" onClick={(e) => e.stopPropagation()}>
                  <div className="modal-title">{confirmDialog.title}</div>
                  <div className="modal-message">{confirmDialog.message}</div>

                  <div className="modal-actions">
                    <button onClick={closeConfirmDialog}>取消</button>
                    <button
                      className="danger-button"
                      onClick={async () => {
                        const action = confirmDialog.action;
                        closeConfirmDialog();

                        if (action === "save1") {
                          await runAction(() => saveToSlot(1));
                          return;
                        }
                        if (action === "save2") {
                          await runAction(() => saveToSlot(2));
                          return;
                        }
                        if (action === "save3") {
                          await runAction(() => saveToSlot(3));
                          return;
                        }

                        if (action === "load1") {
                          await runAction(() => loadFromSlot(1));
                          return;
                        }
                        if (action === "load2") {
                          await runAction(() => loadFromSlot(2));
                          return;
                        }
                        if (action === "load3") {
                          await runAction(() => loadFromSlot(3));
                          return;
                        }

                        if (action === "restart") {
                          await runAction(restartGame);
                          return;
                        }

                        if (action === "confirm-pending") {
                          await runAction(confirmPending);
                          return;
                        }

                        if (action === "endgame") {
                          await runAction(endGameByAgreement);
                          return;
                        }

                        if (action === "resign") {
                          await runAction(resignGame);
                          return;
                        }
                      }}
                    >
                      确认
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
        {payload?.game_over ? (
          <div className="modal-mask modal-mask-top">
            <div className="modal-card modal-card-gameover" onClick={(e) => e.stopPropagation()}>
              <div className="modal-title">游戏结束</div>

              <div className="gameover-winner">
                {payload.winner === "R"
                  ? "红方获胜"
                  : payload.winner === "B"
                  ? "蓝方获胜"
                  : "平局"}
              </div>

              <div className="gameover-reason">
                结束原因：{payload.game_over_reason ?? "未知"}
              </div>

              <div className="modal-actions">
                <button
                  onClick={() =>
                    openConfirmDialog("确认重开", "是否确认重新开始当前对局？", "restart")
                  }
                >
                  重开
                </button>
                <button onClick={() => openModal("save-load")}>存档</button>
                <button onClick={() => runAction(exportRecord)}>导出棋谱</button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}