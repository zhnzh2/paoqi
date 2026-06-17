/**
 * Pyodide 引擎 —— 在浏览器中本地运行炮棋核心规则引擎。
 *
 * 特性：
 * - 从 jsDelivr CDN 加载 Pyodide 运行时
 * - 阶段性进度报告（百分比 + 文字描述）
 * - IndexedDB 缓存完整性检查，损坏时自动清理重试
 * - 版本号变更时自动清理旧缓存
 */

import CORE_MODULES from "./coreModules";
import type { GameAction, GamePayload } from "../types/game";

// ---------- 常量 ----------

const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js";
const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";

/** 引擎版本号——修改此值会触发清理所有旧缓存 */
const ENGINE_VERSION = "1.0.0";
const LS_VERSION_KEY = "paoqi_engine_version";
const PYODIDE_IDB_NAME = "/pyodide";

// ---------- 类型 ----------

export interface EngineProgress {
  stage: string;       // 当前阶段描述
  percent: number;     // 0-100
}

export type EngineProgressCallback = (progress: EngineProgress) => void;

export interface EngineApplyResult {
  ok: boolean;
  message: string;
  result?: Record<string, any>;
  payload?: GamePayload;
}

export interface EnginePreviewResult {
  ok: boolean;
  message: string;
  preview_snapshot?: Record<string, any> | null;
  result?: Record<string, any>;
}

// ---------- Python 辅助脚本 ----------

const PYTHON_HELPER = `
from core.game import Game
from core.save_io import load_game_from_file as _load_game_from_file
import json as _json

_game = None

def _ensure():
    global _game
    if _game is None:
        _game = Game()

def _payload(g=None):
    g = g or _game
    return {
        "snapshot": g.get_state_snapshot(),
        "legal_actions": g.get_legal_actions(),
        "legal_actions_snapshot": g.get_legal_actions_snapshot(),
        "has_pending_auto_action": g.has_pending_auto_action(),
        "pending_auto_action": g.pending_auto_action,
        "pending_auto_message": g.pending_auto_message,
        "auto_action_messages": list(g.auto_action_messages),
        "game_over": g.game_over,
        "game_over_reason": g.game_over_reason,
        "winner": g.winner,
        "history": list(g.history),
        "turn_number": g.turn_number,
        "current_player": g.current_player,
        "phase": g.phase,
    }

def engine_new_game():
    global _game
    _game = Game()
    return _payload()

def engine_get_payload():
    _ensure()
    return _payload()

def engine_apply_action(action):
    _ensure()
    result = _game.try_apply_action_with_snapshot(action)
    if not result["ok"]:
        return {"ok": False, "message": result["message"]}
    pl = result.get("result", {})
    return {
        "ok": True,
        "message": "操作成功：" + str(pl.get("action_text", "ok")),
        "result": pl,
        "payload": _payload(),
    }

def engine_preview_action(action):
    _ensure()
    try:
        pg = _game.clone()
        result = pg.try_apply_action_with_snapshot(action)
        if not result["ok"]:
            return {"ok": False, "message": result["message"]}
        pl = result.get("result", {})
        return {
            "ok": True,
            "message": "preview ok",
            "preview_snapshot": pl.get("after"),
            "result": pl,
        }
    except Exception as e:
        return {"ok": False, "message": str(e)}

def engine_confirm_pending():
    _ensure()
    if not _game.has_pending_auto_action():
        return {"ok": False, "message": "当前没有待确认的自动动作。"}
    pending = _game.pending_auto_action
    if pending is None:
        return {"ok": False, "message": "待确认动作不存在。"}
    result = _game.try_apply_action_with_snapshot(pending)
    if not result["ok"]:
        return {"ok": False, "message": result["message"]}
    pl = result.get("result", {})
    return {
        "ok": True,
        "message": "操作成功：" + str(pl.get("action_text", "ok")),
        "result": pl,
        "payload": _payload(),
    }

def engine_undo():
    _ensure()
    try:
        _game.undo()
        return {"ok": True, "message": "已撤销上一步操作。", "payload": _payload()}
    except Exception as e:
        return {"ok": False, "message": "撤销失败：" + str(e)}

def engine_restart():
    global _game
    _game = Game()
    return _payload()

def engine_endgame():
    _ensure()
    try:
        _game.finish_by_agreement()
        return {"ok": True, "message": "已确认终局。", "payload": _payload()}
    except Exception as e:
        return {"ok": False, "message": "终局失败：" + str(e)}

def engine_resign():
    _ensure()
    try:
        _game.resign()
        return {"ok": True, "message": "已确认投降。", "payload": _payload()}
    except Exception as e:
        return {"ok": False, "message": "投降失败：" + str(e)}

def engine_export_state():
    _ensure()
    from core.state_io import export_full_state
    return export_full_state(_game)

def engine_import_state(data):
    global _game
    from core.state_io import from_exported_state
    _game = from_exported_state(data)
    return _payload()

def engine_get_history_count():
    _ensure()
    return len(_game.history)
`.trim();

// ---------- 工具函数 ----------

/**
 * 删除 Pyodide 的 IndexedDB 缓存（用于清理损坏的缓存）。
 */
function clearPyodideCache(): Promise<void> {
  return new Promise((resolve) => {
    try {
      const req = indexedDB.deleteDatabase(PYODIDE_IDB_NAME);
      req.onsuccess = () => resolve();
      req.onerror = () => resolve();   // 数据库不存在也算成功
      req.onblocked = () => {
        // 被其他标签页占用，强制关闭后重试
        console.warn("Pyodide 缓存被占用，跳过清理");
        resolve();
      };
    } catch {
      // indexedDB 不可用（极端隐私模式），忽略
      resolve();
    }
  });
}

/**
 * 检查是否需要清理旧版本缓存。
 * 如果上次记录的引擎版本与当前不同，清理缓存并更新版本号。
 */
async function invalidateStaleCache(): Promise<void> {
  const storedVersion = localStorage.getItem(LS_VERSION_KEY);
  if (storedVersion !== ENGINE_VERSION) {
    console.log(`引擎版本变更 (${storedVersion} → ${ENGINE_VERSION})，清理旧缓存...`);
    await clearPyodideCache();
    localStorage.setItem(LS_VERSION_KEY, ENGINE_VERSION);
  }
}

// ---------- 引擎类 ----------

declare global {
  interface Window {
    loadPyodide?: any;
  }
}

export class PaoqiEngine {
  private pyodide: any = null;
  private ready = false;

  private constructor() {}

  /**
   * 创建并初始化引擎。
   * @param onProgress 进度回调，接收 { stage, percent }
   */
  static async create(onProgress?: EngineProgressCallback): Promise<PaoqiEngine> {
    const engine = new PaoqiEngine();
    await engine.init(onProgress);
    return engine;
  }

  private report(onProgress: EngineProgressCallback | undefined, stage: string, percent: number): void {
    onProgress?.({ stage, percent });
  }

  private async init(onProgress?: EngineProgressCallback): Promise<void> {
    // 1. 检查并清理版本不匹配的旧缓存
    this.report(onProgress, "正在检查缓存...", 0);
    await invalidateStaleCache();

    // 2. 加载 Pyodide CDN 脚本
    this.report(onProgress, "正在连接 CDN...", 5);
    await this.loadPyodideScript();

    // 3. 下载并初始化 Pyodide 核心运行时
    this.report(onProgress, "正在下载运行时...", 15);

    try {
      this.pyodide = await window.loadPyodide({
        indexURL: PYODIDE_INDEX_URL,
      });
    } catch (firstError) {
      // 首次加载失败——可能是缓存损坏，清理后重试一次
      console.warn("Pyodide 首次加载失败，清理缓存后重试...", firstError);
      this.report(onProgress, "首次加载失败，正在清理损坏缓存...", 10);
      await clearPyodideCache();

      try {
        this.pyodide = await window.loadPyodide({
          indexURL: PYODIDE_INDEX_URL,
        });
      } catch (secondError) {
        throw new Error(
          `Pyodide 运行时加载失败（已重试）。请检查网络连接。\n` +
          `错误详情：${String(secondError)}`
        );
      }
    }

    // 4. 初始化 Python 环境
    this.report(onProgress, "正在初始化 Python 环境...", 50);

    this.pyodide.runPython(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
`);

    // 5. 写入 core/ 模块到虚拟文件系统
    this.report(onProgress, "正在加载规则引擎模块...", 65);
    this.writeCoreModules();

    // 6. 执行 Python 辅助脚本
    this.report(onProgress, "正在编译游戏引擎...", 85);
    this.pyodide.runPython(PYTHON_HELPER);

    // 7. 完成
    this.report(onProgress, "引擎就绪", 100);
    this.ready = true;
  }

  private loadPyodideScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (window.loadPyodide) {
        resolve();
        return;
      }

      const script = document.createElement("script");
      script.src = PYODIDE_CDN;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(
        "Pyodide CDN 连接失败。\n" +
        "可能原因：网络不通、CDN 被屏蔽、或浏览器插件拦截。\n" +
        `CDN 地址：${PYODIDE_CDN}`
      ));
      document.head.appendChild(script);
    });
  }

  private writeCoreModules(): void {
    const FS = this.pyodide.FS;

    try { FS.mkdir("/home/pyodide/core"); } catch (_) { /* 已存在 */ }
    try { FS.mkdir("/home/pyodide/core/game_impl"); } catch (_) { /* 已存在 */ }

    for (const [relativePath, content] of Object.entries(CORE_MODULES)) {
      const targetPath = `/home/pyodide/core/${relativePath}`;
      FS.writeFile(targetPath, content, { encoding: "utf8" });
    }
  }

  get isReady(): boolean { return this.ready; }

  private run<T = any>(code: string): T {
    if (!this.ready) throw new Error("引擎尚未就绪。");
    return this.pyodide.runPython(code) as T;
  }

  // ===================== 公开 API =====================

  newGame(): GamePayload {
    return this.run<GamePayload>("engine_new_game()");
  }

  getPayload(): GamePayload {
    return this.run<GamePayload>("engine_get_payload()");
  }

  applyAction(action: GameAction): EngineApplyResult {
    (this.pyodide.globals as any).set("_js_action", action);
    return this.run<EngineApplyResult>("engine_apply_action(_js_action)");
  }

  previewAction(action: GameAction): EnginePreviewResult {
    (this.pyodide.globals as any).set("_js_action", action);
    return this.run<EnginePreviewResult>("engine_preview_action(_js_action)");
  }

  confirmPending(): EngineApplyResult {
    return this.run<EngineApplyResult>("engine_confirm_pending()");
  }

  undo(): { ok: boolean; message: string; payload?: GamePayload } {
    return this.run("engine_undo()");
  }

  restart(): GamePayload {
    return this.run<GamePayload>("engine_restart()");
  }

  endGameByAgreement(): { ok: boolean; message: string; payload?: GamePayload } {
    return this.run("engine_endgame()");
  }

  resign(): { ok: boolean; message: string; payload?: GamePayload } {
    return this.run("engine_resign()");
  }

  exportState(): Record<string, any> {
    this.run("from core.state_io import export_full_state");
    return this.run("engine_export_state()");
  }

  importState(data: Record<string, any>): GamePayload {
    (this.pyodide.globals as any).set("_js_state", data);
    return this.run<GamePayload>("engine_import_state(_js_state)");
  }

  getHistoryCount(): number {
    return this.run<number>("engine_get_history_count()");
  }
}
