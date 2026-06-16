/**
 * Pyodide 引擎 —— 在浏览器中本地运行炮棋核心规则引擎。
 *
 * 工作方式：
 * 1. 从 jsDelivr CDN 加载 Pyodide
 * 2. 将打包好的 core/ 模块写入虚拟文件系统
 * 3. 注入 Python 辅助函数，暴露为 TypeScript 方法
 * 4. 所有游戏逻辑在浏览器本地毫秒级完成
 */

import CORE_MODULES from "./coreModules";
import type { GameAction, GamePayload } from "../types/game";

// ---------- 类型定义 ----------

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

export type EngineProgressCallback = (message: string) => void;

// ---------- Python 辅助脚本 ----------

/**
 * 注入 Pyodide 的 Python 辅助脚本。
 * 负责管理 Game 实例并提供 JS 可调用的函数。
 */
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
    """action 是 JS 传入的 dict。返回 {ok, message, result, payload}"""
    _ensure()
    # Pyodide 自动将 JS object 转为 Python dict
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
    """返回 {ok, preview_snapshot, result}"""
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
    """导出完整状态为 JSON 兼容的 dict，用于 save"""
    _ensure()
    from core.state_io import export_full_state
    return export_full_state(_game)

def engine_import_state(data):
    """从 export_full_state 的 dict 恢复游戏"""
    global _game
    from core.state_io import from_exported_state
    _game = from_exported_state(data)
    return _payload()

def engine_get_history_count():
    _ensure()
    return len(_game.history)
`.trim();


// ---------- 引擎单例 ----------

const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js";

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
   * 初始化引擎：加载 Pyodide → 写入 core 模块 → 执行 Python 辅助脚本。
   * 这是一个重型操作（首次需下载 ~10-15MB），应在应用启动时调用一次。
   */
  static async create(onProgress?: EngineProgressCallback): Promise<PaoqiEngine> {
    const engine = new PaoqiEngine();
    await engine.init(onProgress);
    return engine;
  }

  private async init(onProgress?: EngineProgressCallback): Promise<void> {
    const log = (msg: string) => onProgress?.(msg);

    // 1. 加载 Pyodide 脚本
    log("正在加载 Pyodide 运行时...");
    await this.loadPyodideScript();

    // 2. 初始化 Pyodide
    log("正在初始化 Python 环境...");
    this.pyodide = await window.loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/",
    });

    // 3. 将 core/ 模块写入虚拟文件系统
    log("正在加载核心规则引擎模块...");
    this.writeCoreModules();

    // 4. 在 Python 环境中添加路径
    this.pyodide.runPython(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
`);

    // 5. 执行辅助脚本
    log("正在初始化游戏引擎...");
    this.pyodide.runPython(PYTHON_HELPER);

    this.ready = true;
    log("引擎就绪。");
  }

  /**
   * 动态加载 Pyodide CDN 脚本。
   */
  private loadPyodideScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      // 检查是否已加载
      if (window.loadPyodide) {
        resolve();
        return;
      }

      const script = document.createElement("script");
      script.src = PYODIDE_CDN;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Pyodide CDN 加载失败，请检查网络连接。"));
      document.head.appendChild(script);
    });
  }

  /**
   * 将打包的 core/ 模块写入 Pyodide 虚拟文件系统。
   */
  private writeCoreModules(): void {
    const FS = this.pyodide.FS;

    // 确保目标目录存在
    try { FS.mkdir("/home/pyodide/core"); } catch (_) { /* 已存在 */ }
    try { FS.mkdir("/home/pyodide/core/game_impl"); } catch (_) { /* 已存在 */ }

    for (const [relativePath, content] of Object.entries(CORE_MODULES)) {
      const targetPath = `/home/pyodide/core/${relativePath}`;
      FS.writeFile(targetPath, content, { encoding: "utf8" });
    }
  }

  /** 检查引擎是否已就绪 */
  get isReady(): boolean {
    return this.ready;
  }

  /**
   * 在 Python 环境中执行代码并返回结果。
   */
  private run<T = any>(code: string): T {
    if (!this.ready) {
      throw new Error("引擎尚未就绪。");
    }
    return this.pyodide.runPython(code) as T;
  }

  // ===================== 公开 API =====================

  /** 创建新对局，返回初始 GamePayload */
  newGame(): GamePayload {
    return this.run<GamePayload>("engine_new_game()");
  }

  /** 获取当前对局的完整 GamePayload */
  getPayload(): GamePayload {
    return this.run<GamePayload>("engine_get_payload()");
  }

  /** 执行动作，返回结果 + 更新后的 GamePayload */
  applyAction(action: GameAction): EngineApplyResult {
    // 将 JS 对象作为 Python dict 参数传递
    (this.pyodide.globals as any).set("_js_action", action);
    const result = this.run<EngineApplyResult>(
      "engine_apply_action(_js_action)"
    );
    return result;
  }

  /** 预览动作效果，不改变当前游戏状态 */
  previewAction(action: GameAction): EnginePreviewResult {
    (this.pyodide.globals as any).set("_js_action", action);
    return this.run<EnginePreviewResult>(
      "engine_preview_action(_js_action)"
    );
  }

  /** 确认待处理的自动动作 */
  confirmPending(): EngineApplyResult {
    return this.run<EngineApplyResult>("engine_confirm_pending()");
  }

  /** 撤销上一步 */
  undo(): { ok: boolean; message: string; payload?: GamePayload } {
    return this.run("engine_undo()");
  }

  /** 重新开始对局 */
  restart(): GamePayload {
    return this.run<GamePayload>("engine_restart()");
  }

  /** 协商终局 */
  endGameByAgreement(): { ok: boolean; message: string; payload?: GamePayload } {
    return this.run("engine_endgame()");
  }

  /** 投降 */
  resign(): { ok: boolean; message: string; payload?: GamePayload } {
    return this.run("engine_resign()");
  }

  /** 导出完整状态（用于保存到 localStorage） */
  exportState(): Record<string, any> {
    this.run("from core.state_io import export_full_state");
    return this.run("engine_export_state()");
  }

  /** 从导出状态恢复 */
  importState(data: Record<string, any>): GamePayload {
    (this.pyodide.globals as any).set("_js_state", data);
    return this.run<GamePayload>("engine_import_state(_js_state)");
  }

  /** 获取棋谱长度（用于判断是否可继续） */
  getHistoryCount(): number {
    return this.run<number>("engine_get_history_count()");
  }
}
