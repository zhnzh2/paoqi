from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.game import Game
from ui.save_io import (
    export_record_to_file,
    load_game_from_file,
    save_game_to_file,
)
from web.backend.adapters import (
    build_error_response,
    build_game_payload,
    build_ok_response,
)
from web.backend.schemas import ActionRequest
from web.backend.session_store import LocalGameSession


BASE_DIR = Path(__file__).resolve().parents[2]
SAVE_DIR = BASE_DIR / "saves"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

SAVE_SLOT_FILES = {
    1: str(SAVE_DIR / "web_save_slot_1.json"),
    2: str(SAVE_DIR / "web_save_slot_2.json"),
    3: str(SAVE_DIR / "web_save_slot_3.json"),
}

RECORD_EXPORT_FILE = str(SAVE_DIR / "web_record_export.txt")

app = FastAPI(title="Paoqi Web Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = LocalGameSession()


@app.get("/api/health")
def health_check() -> dict:
    return {
        "ok": True,
        "message": "backend is running",
    }


@app.post("/api/new-game")
def new_game() -> dict:
    game = session.reset()
    return build_ok_response(game, message="已开始新对局。")


@app.get("/api/state")
def get_state() -> dict:
    game = session.get_game()
    return build_ok_response(game)


@app.post("/api/apply-action")
def apply_action(req: ActionRequest) -> dict:
    game = session.get_game()
    result = game.try_apply_action_with_snapshot(req.action)

    if not result["ok"]:
        return build_error_response(result["message"])

    payload = result.get("result", {})
    return build_ok_response(
        game,
        message=f"操作成功：{payload.get('action_text', 'ok')}",
        extra={
            "result": payload,
        },
    )


@app.post("/api/confirm-pending")
def confirm_pending_action() -> dict:
    game = session.get_game()

    if not game.has_pending_auto_action():
        return build_error_response("当前没有待确认的自动动作。")

    pending = game.pending_auto_action
    if pending is None:
        return build_error_response("待确认动作不存在。")

    result = game.try_apply_action_with_snapshot(pending)
    if not result["ok"]:
        return build_error_response(result["message"])

    payload = result.get("result", {})
    return build_ok_response(
        game,
        message=f"操作成功：{payload.get('action_text', 'ok')}",
        extra={
            "result": payload,
        },
    )


@app.post("/api/restart")
def restart_game() -> dict:
    game = Game()
    session.set_game(game)
    return build_ok_response(game, message="已重新开始对局。")


@app.post("/api/undo")
def undo_action() -> dict:
    game = session.get_game()

    try:
        game.undo()
        return build_ok_response(game, message="已撤销上一步操作。")
    except Exception as e:
        return build_error_response(f"撤销失败：{e}")

@app.post("/api/endgame")
def finish_by_agreement() -> dict:
    game = session.get_game()

    try:
        game.finish_by_agreement()
        return build_ok_response(game, message="已确认终局。")
    except Exception as e:
        return build_error_response(f"终局失败：{e}")


@app.post("/api/resign")
def resign_game() -> dict:
    game = session.get_game()

    try:
        game.resign()
        return build_ok_response(game, message="已确认投降。")
    except Exception as e:
        return build_error_response(f"投降失败：{e}")

@app.post("/api/save/{slot}")
def save_to_slot(slot: int) -> dict:
    game = session.get_game()

    if slot not in SAVE_SLOT_FILES:
        return build_error_response("无效的存档槽位。")

    try:
        save_game_to_file(game, SAVE_SLOT_FILES[slot])
        return build_ok_response(game, message=f"已保存到槽位 {slot}。")
    except Exception as e:
        return build_error_response(f"保存失败：{e}")


@app.post("/api/load/{slot}")
def load_from_slot(slot: int) -> dict:
    if slot not in SAVE_SLOT_FILES:
        return build_error_response("无效的存档槽位。")

    try:
        game = load_game_from_file(SAVE_SLOT_FILES[slot])
        session.set_game(game)
        return build_ok_response(game, message=f"已从槽位 {slot} 载入对局。")
    except Exception as e:
        return build_error_response(f"读档失败：{e}")


@app.get("/api/export-record")
def export_record() -> dict:
    game = session.get_game()

    try:
        export_record_to_file(game, RECORD_EXPORT_FILE)
        return {
            "ok": True,
            "message": f"已导出棋谱到 {RECORD_EXPORT_FILE}",
            "path": RECORD_EXPORT_FILE,
            "history": list(game.history),
            "data": build_game_payload(game),
        }
    except Exception as e:
        return build_error_response(f"导出失败：{e}")