"""对局记录保存模块 —— 终局时将对局数据写入 data/records/ 目录。

每个对局一个专属文件夹，命名格式：{时间戳_ms}_{房间码}
包含：棋谱 record.txt、房间信息 info.json、聊天记录 chat.json、逐步回放 steps.json
"""

from __future__ import annotations

from copy import deepcopy
import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from core.game import Game
from core.state_io import get_board_snapshot

BASE_DIR = Path(__file__).resolve().parents[2]
RECORDS_DIR = BASE_DIR / "data" / "records"
SAFE_FOLDER_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")

_index_lock = threading.Lock()
_index_mtime_ns = -1
_records_by_uid: dict[int, list[dict[str, Any]]] = {}


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _timestamp_folder(room_code: str) -> str:
    """生成以当前时间（精确到毫秒）命名的文件夹名。"""
    local_now = datetime.now()
    ts_ms = (
        local_now.strftime("%Y-%m-%d_%H-%M-%S")
        + f".{local_now.microsecond // 1000:03d}"
    )
    return f"{ts_ms}_{room_code}"


def _compact_board(game: Game) -> list[list[dict[str, Any] | None]]:
    return [
        [
            {"color": cell["color"], "level": cell["level"]}
            if cell
            else None
            for cell in row
        ]
        for row in get_board_snapshot(game)
    ]


def _record_folder(folder_name: str) -> Path | None:
    """将客户端传入的记录名约束在 records 目录的直接子目录中。"""
    if (
        not folder_name
        or folder_name in {".", ".."}
        or not SAFE_FOLDER_NAME.fullmatch(folder_name)
    ):
        return None

    root = RECORDS_DIR.resolve()
    folder = (root / folder_name).resolve()
    if folder.parent != root:
        return None
    return folder


def _build_steps(action_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """重放动作历史，生成每一步的棋盘快照和描述。"""
    replay_game = Game()
    steps: list[dict[str, Any]] = []

    for entry in action_history:
        action = entry.get("action", entry)
        actor_color = entry.get("actor_color")
        result = replay_game.try_apply_action_with_snapshot(action)
        if not result["ok"]:
            break

        payload = result.get("result", {})
        steps.append({
            "step": len(steps) + 1,
            "action_text": payload.get("action_text", ""),
            "action_type": action.get("type", "?"),
            "actor_color": actor_color,
            "current_player": replay_game.current_player,
            "phase": replay_game.phase,
            "board": _compact_board(replay_game),
        })

    return steps


def _invalidate_record_index() -> None:
    global _index_mtime_ns
    with _index_lock:
        _index_mtime_ns = -1


def save_game_record(
    room_code: str,
    game: Game,
    red_info: dict[str, Any],
    blue_info: dict[str, Any],
    chat_history: list[dict[str, Any]],
    action_history: list[dict[str, Any]],
    game_started_at: float | None,
) -> str | None:
    """保存对局记录到磁盘。返回文件夹路径；失败返回 None。"""

    if not game.game_over:
        return None

    try:
        folder_name = _timestamp_folder(room_code)
        folder = RECORDS_DIR / folder_name
        _ensure_dir(folder)

        # ---------- 棋谱 ----------
        record_path = folder / "record.txt"
        history_text = (
            "\n".join(game.history)
            if game.history
            else "（无棋谱 —— 对局未发生走子即结束）"
        )
        record_path.write_text(history_text, encoding="utf-8")

        # ---------- 终局类型 ----------
        end_type = "normal"
        if game.game_over_reason:
            reason = game.game_over_reason.lower()
            if "投降" in reason or "resign" in reason:
                end_type = "resign"
            elif (
                "协商" in reason
                or "协议" in reason
                or "终局" in reason
                or "agreement" in reason
            ):
                end_type = "agreement"
            else:
                end_type = "normal"

        # ---------- 房间信息 ----------
        info: dict[str, Any] = {
            "room_code": room_code,
            "red": red_info,
            "blue": blue_info,
            "winner": game.winner,
            "end_type": end_type,
            "game_over_reason": game.game_over_reason,
            "turn_number": game.turn_number,
            "created_at": time.time(),
        }
        if game_started_at is not None:
            info["game_started_at"] = game_started_at
            info["duration_seconds"] = round(time.time() - game_started_at, 1)

        info_path = folder / "info.json"
        info_path.write_text(
            json.dumps(info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # ---------- 聊天记录 ----------
        if chat_history:
            chat_path = folder / "chat.json"
            chat_path.write_text(
                json.dumps(deepcopy(chat_history), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        # ---------- 逐步回放数据 ----------
        if action_history:
            steps = _build_steps(deepcopy(action_history))
            steps_path = folder / "steps.json"
            steps_path.write_text(
                json.dumps(steps, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        _invalidate_record_index()
        return str(folder)
    except Exception:
        return None


# ------------------------------------------------------------------
# 查询
# ------------------------------------------------------------------


def _load_record_index() -> dict[int, list[dict[str, Any]]]:
    global _index_mtime_ns, _records_by_uid

    if not RECORDS_DIR.exists():
        return {}

    current_mtime_ns = RECORDS_DIR.stat().st_mtime_ns
    with _index_lock:
        if current_mtime_ns == _index_mtime_ns:
            return _records_by_uid

        index: dict[int, list[dict[str, Any]]] = {}
        for folder in sorted(RECORDS_DIR.iterdir(), reverse=True):
            if not folder.is_dir():
                continue
            info_path = folder / "info.json"
            if not info_path.exists():
                continue

            try:
                info = json.loads(info_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            summary = {
                "folder_name": folder.name,
                "room_code": info.get("room_code", ""),
                "winner": info.get("winner"),
                "end_type": info.get("end_type", "normal"),
                "game_over_reason": info.get("game_over_reason", ""),
                "red": info.get("red"),
                "blue": info.get("blue"),
                "turn_number": info.get("turn_number", 0),
                "duration_seconds": info.get("duration_seconds", 0),
                "created_at": info.get("created_at", 0),
            }
            participant_uids = {
                (info.get("red") or {}).get("uid"),
                (info.get("blue") or {}).get("uid"),
            }
            for participant_uid in participant_uids:
                if isinstance(participant_uid, int) and participant_uid >= 0:
                    index.setdefault(participant_uid, []).append(summary)

        _records_by_uid = index
        _index_mtime_ns = current_mtime_ns
        return _records_by_uid


def list_user_records(uid: int) -> list[dict[str, Any]]:
    """列出某用户参与的所有对局记录。"""
    return [dict(item) for item in _load_record_index().get(uid, [])]


def get_record(folder_name: str) -> dict[str, Any] | None:
    """读取单个对局文件夹的全部数据。"""
    folder = _record_folder(folder_name)
    if folder is None or not folder.is_dir():
        return None

    info_path = folder / "info.json"
    record_path = folder / "record.txt"
    steps_path = folder / "steps.json"
    chat_path = folder / "chat.json"

    if not info_path.exists():
        return None

    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    result: dict[str, Any] = {
        "folder_name": folder_name,
        "info": info,
        "record_text": record_path.read_text(encoding="utf-8") if record_path.exists() else "",
        "initial_board": _compact_board(Game()),
        "steps": [],
        "chat": [],
    }

    if steps_path.exists():
        try:
            result["steps"] = json.loads(steps_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    if chat_path.exists():
        try:
            result["chat"] = json.loads(chat_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return result


def record_belongs_to_user(folder_name: str, uid: int) -> bool:
    folder = _record_folder(folder_name)
    if folder is None:
        return False

    info_path = folder / "info.json"
    if not info_path.is_file():
        return False

    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    return uid in {
        (info.get("red") or {}).get("uid"),
        (info.get("blue") or {}).get("uid"),
    }


def get_record_folder(folder_name: str) -> Path | None:
    folder = _record_folder(folder_name)
    if folder is None or not folder.is_dir():
        return None
    return folder
