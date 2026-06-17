from __future__ import annotations

import os
from pathlib import Path

import json

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.game import Game
from core.save_io import (
    export_record_to_file,
    load_game_from_file,
    save_game_to_file,
)
from web.backend.adapters import (
    build_error_response,
    build_game_payload,
    build_ok_response,
)
from web.backend.schemas import (
    ActionRequest,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UpdateSettingsRequest,
)
from web.backend.session_store import AuthSession, LocalGameSession
from web.backend.user_store import (
    authenticate_user,
    change_user_password,
    get_user_by_uid,
    get_user_settings,
    register_user,
    save_user_settings,
    update_user_profile,
)
from web.backend.room_manager import RoomManager

BASE_DIR = Path(__file__).resolve().parents[2]
SAVE_DIR = BASE_DIR / "saves"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

SAVE_SLOT_FILES = {
    1: str(SAVE_DIR / "web_save_slot_1.json"),
    2: str(SAVE_DIR / "web_save_slot_2.json"),
    3: str(SAVE_DIR / "web_save_slot_3.json"),
}

RECORD_EXPORT_FILE = str(SAVE_DIR / "web_record_export.txt")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "PAOQI_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,https://paoqi.org,https://www.paoqi.org",
    ).split(",")
    if origin.strip()
]

app = FastAPI(title="Paoqi Web Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = LocalGameSession()
auth_session = AuthSession()
room_manager = RoomManager()


def require_auth(
    token: str | None = Header(default=None, alias="X-Paoqi-Auth-Token"),
) -> int:
    """依赖项：要求请求携带有效的认证令牌，返回 uid。"""
    if token is None:
        raise HTTPException(status_code=401, detail="需要登录")
    uid = auth_session.validate_token(token)
    if uid is None:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    return uid


def get_session_id(
    x_paoqi_session_id: str | None = Header(default=None, alias="X-Paoqi-Session-Id"),
) -> str | None:
    return x_paoqi_session_id

@app.get("/api/health")
def health_check() -> dict:
    return {
        "ok": True,
        "message": "backend is running",
    }

@app.post("/api/new-game")
def new_game(session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.reset(session_id)
    return build_ok_response(game, message="已开始新对局。")

@app.get("/api/state")
def get_state(session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)
    return build_ok_response(game)

@app.post("/api/apply-action")
def apply_action(req: ActionRequest, session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)
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

@app.post("/api/preview-action")
def preview_action(req: ActionRequest, session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)

    try:
        preview_game = game.clone()
        result = preview_game.try_apply_action_with_snapshot(req.action)

        if not result["ok"]:
            return build_error_response(result["message"])

        payload = result.get("result", {})
        return {
            "ok": True,
            "message": "preview ok",
            "preview_snapshot": payload.get("after"),
            "result": payload,
        }
    except Exception as e:
        return build_error_response(f"预览失败：{e}")

@app.post("/api/confirm-pending")
def confirm_pending_action(session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)

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
def restart_game(session_id: str | None = Depends(get_session_id)) -> dict:
    game = Game()
    session.set_game(game, session_id)
    return build_ok_response(game, message="已重新开始对局。")

@app.post("/api/undo")
def undo_action(session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)

    try:
        game.undo()
        return build_ok_response(game, message="已撤销上一步操作。")
    except Exception as e:
        return build_error_response(f"撤销失败：{e}")

@app.post("/api/endgame")
def finish_by_agreement(session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)

    try:
        game.finish_by_agreement()
        return build_ok_response(game, message="已确认终局。")
    except Exception as e:
        return build_error_response(f"终局失败：{e}")

@app.post("/api/resign")
def resign_game(session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)

    try:
        game.resign()
        return build_ok_response(game, message="已确认投降。")
    except Exception as e:
        return build_error_response(f"投降失败：{e}")

@app.post("/api/save/{slot}")
def save_to_slot(slot: int, session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)

    if slot not in SAVE_SLOT_FILES:
        return build_error_response("无效的存档槽位。")

    try:
        save_game_to_file(game, SAVE_SLOT_FILES[slot])
        return build_ok_response(game, message=f"已保存到槽位 {slot}。")
    except Exception as e:
        return build_error_response(f"保存失败：{e}")

@app.post("/api/load/{slot}")
def load_from_slot(slot: int, session_id: str | None = Depends(get_session_id)) -> dict:
    if slot not in SAVE_SLOT_FILES:
        return build_error_response("无效的存档槽位。")

    try:
        game = load_game_from_file(SAVE_SLOT_FILES[slot])
        session.set_game(game, session_id)
        return build_ok_response(game, message=f"已从槽位 {slot} 载入对局。")
    except Exception as e:
        return build_error_response(f"读档失败：{e}")

@app.get("/api/export-record")
def export_record(session_id: str | None = Depends(get_session_id)) -> dict:
    game = session.get_game(session_id)

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
    
@app.get("/api/save-slots")
def get_save_slots(session_id: str | None = Depends(get_session_id)) -> dict:
    slots = []

    for slot, path in SAVE_SLOT_FILES.items():
        p = Path(path)
        slots.append(
            {
                "slot": slot,
                "exists": p.exists(),
                "updated_at": p.stat().st_mtime if p.exists() else None,
            }
        )

    game = session.get_game(session_id)
    can_continue = len(game.history) > 0 and not game.game_over

    return {
        "ok": True,
        "message": "ok",
        "data": {
            "can_continue": can_continue,
            "slots": slots,
            "game_over": game.game_over,
            "history_count": len(game.history),
        },
    }


# -------------------- 房间端点 --------------------


@app.post("/api/rooms")
def create_room(uid: int = Depends(require_auth)) -> dict:
    """创建联机房间，返回房间码。"""
    profile = get_user_by_uid(uid)
    username = profile["username"] if profile else f"用户{uid}"
    code = room_manager.create_room(uid, username)
    return {
        "ok": True,
        "message": "房间已创建",
        "data": {"room_code": code},
    }


@app.get("/api/rooms")
def list_rooms(uid: int = Depends(require_auth)) -> dict:
    """列出所有可加入的房间。"""
    rooms = room_manager.list_rooms()
    return {
        "ok": True,
        "message": "ok",
        "data": {"rooms": rooms},
    }


# -------------------- WebSocket 端点 --------------------


async def _send_json(ws: WebSocket, data: dict) -> None:
    """安全地向一个 WebSocket 发送 JSON。"""
    try:
        await ws.send_json(data)
    except Exception:
        pass  # 客户端可能已断开


async def _broadcast(room, data: dict) -> None:
    """向房间内所有已连接的玩家广播消息。"""
    if room.red_ws and room.red_connected:
        await _send_json(room.red_ws, data)
    if room.blue_ws and room.blue_connected:
        await _send_json(room.blue_ws, data)


async def _handle_ws_message(room, uid: int, data: dict) -> None:
    """分发单条 WebSocket 消息。"""
    msg_type = data.get("type", "")

    # ---------- 游戏动作 ----------
    if msg_type == "game:action":
        # 验证回合
        color = room.get_color(uid)
        if color != room.game.current_player:
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": "当前不是你的回合"},
            )
            return

        action = data.get("action", {})
        result = room.game.try_apply_action_with_snapshot(action)

        if not result["ok"]:
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": result["message"]},
            )
            return

        payload = build_game_payload(room.game)
        await _broadcast(room, {"type": "game:state", "payload": payload})

    # ---------- 确认自动动作 ----------
    elif msg_type == "game:confirm_pending":
        color = room.get_color(uid)
        if color != room.game.current_player:
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": "当前不是你的回合"},
            )
            return

        if not room.game.has_pending_auto_action():
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": "当前没有待确认的自动动作"},
            )
            return

        pending = room.game.pending_auto_action
        if pending is None:
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": "待确认动作不存在"},
            )
            return

        result = room.game.try_apply_action_with_snapshot(pending)
        if not result["ok"]:
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": result["message"]},
            )
            return

        payload = build_game_payload(room.game)
        await _broadcast(room, {"type": "game:state", "payload": payload})

    # ---------- 协商终局 ----------
    elif msg_type == "game:endgame":
        try:
            room.game.finish_by_agreement()
            payload = build_game_payload(room.game)
            await _broadcast(room, {"type": "game:state", "payload": payload})
        except Exception as e:
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": f"终局失败：{e}"},
            )

    # ---------- 投降 ----------
    elif msg_type == "game:resign":
        try:
            room.game.resign()
            payload = build_game_payload(room.game)
            await _broadcast(room, {"type": "game:state", "payload": payload})
        except Exception as e:
            await _send_json(
                room.get_ws(uid),
                {"type": "game:error", "message": f"投降失败：{e}"},
            )

    # ---------- 心跳 ----------
    elif msg_type == "ping":
        ws = room.get_ws(uid)
        if ws:
            await _send_json(ws, {"type": "pong"})

    # ---------- 聊天 ----------
    elif msg_type == "chat:send":
        text = str(data.get("text", ""))[:50]  # 最多 50 字符
        if not text.strip():
            return
        color = room.get_color(uid)
        profile = get_user_by_uid(uid)
        sender_name = profile["username"] if profile else f"用户{uid}"
        await _broadcast(room, {
            "type": "chat:message",
            "sender": sender_name,
            "color": color,
            "text": text,
        })

    else:
        await _send_json(
            room.get_ws(uid),
            {"type": "game:error", "message": f"未知消息类型：{msg_type}"},
        )


@app.websocket("/ws/room/{room_code}")
async def room_websocket(
    websocket: WebSocket,
    room_code: str,
    token: str = Query(...),
):
    """房间 WebSocket 端点 —— 处理实时通信。"""
    # 1. 验证 token
    uid = auth_session.validate_token(token)
    if uid is None:
        await websocket.close(code=4001, reason="认证失败")
        return

    profile = get_user_by_uid(uid)
    username = profile["username"] if profile else f"用户{uid}"

    # 2. 查找 / 加入房间
    room = room_manager.get_room(room_code)
    if room is None:
        await websocket.close(code=4004, reason="房间不存在")
        return

    # 3. 确认玩家属于该房间
    color = room.get_color(uid)
    is_new_blue = False

    if color is None:
        # 不在房间中，尝试作为蓝方加入
        if room.is_full:
            await websocket.close(code=4003, reason="房间已满")
            return
        try:
            room_manager.join_room(room_code, uid, username)
            color = "B"
            is_new_blue = True
        except ValueError as e:
            await websocket.close(code=4003, reason=str(e))
            return

    # 4. 绑定 WebSocket
    room.set_ws(uid, websocket)
    await websocket.accept()

    # 5. 发送初始状态
    players = room.get_players_info()

    if not room.is_full:
        # 等待对手
        await _send_json(websocket, {
            "type": "room:waiting_opponent",
            "room_code": room_code,
            "color": color,
            "players": players,
        })
    else:
        # 房间已满，发送完整状态
        payload = build_game_payload(room.game)
        await _send_json(websocket, {
            "type": "room:joined",
            "room_code": room_code,
            "color": color,
            "players": players,
            "payload": payload,
        })

        # 如果是新加入的蓝方，通知红方
        if is_new_blue and room.red_ws and room.red_connected:
            await _send_json(room.red_ws, {
                "type": "room:player_joined",
                "player": {"uid": uid, "username": username, "color": "B"},
            })
            # 红方也需要最新状态
            payload = build_game_payload(room.game)
            await _send_json(room.red_ws, {
                "type": "game:state",
                "payload": payload,
            })

    # 如果是重连，通知对手
    if not is_new_blue:
        opponent_ws = room.blue_ws if color == "R" else room.red_ws
        if opponent_ws:
            await _send_json(opponent_ws, {"type": "opponent:reconnected"})

    # 6. 消息循环
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await _send_json(websocket, {"type": "game:error", "message": "无效的 JSON"})
                continue
            await _handle_ws_message(room, uid, data)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # 7. 断开处理
        room.mark_disconnected(uid)
        # 通知对手
        opponent_ws = room.blue_ws if color == "R" else room.red_ws
        if opponent_ws:
            await _send_json(opponent_ws, {"type": "opponent:disconnected"})


# -------------------- 认证端点 --------------------


@app.post("/api/auth/register")
def register(req: RegisterRequest) -> dict:
    """注册新用户。"""
    if req.password != req.confirm_password:
        return build_error_response("两次输入的密码不一致")

    try:
        profile = register_user(req.username, req.password, req.intro_letter)
    except ValueError as e:
        return build_error_response(str(e))

    token = auth_session.create_token(profile["uid"])
    return {
        "ok": True,
        "message": "注册成功",
        "data": {
            "token": token,
            "user": profile,
        },
    }


@app.post("/api/auth/login")
def login(req: LoginRequest) -> dict:
    """用户登录。"""
    profile = authenticate_user(req.username, req.password)
    if profile is None:
        return build_error_response("用户名或密码错误")

    token = auth_session.create_token(profile["uid"])
    return {
        "ok": True,
        "message": "登录成功",
        "data": {
            "token": token,
            "user": profile,
        },
    }


@app.get("/api/auth/me")
def get_current_user(
    token: str | None = Header(default=None, alias="X-Paoqi-Auth-Token"),
) -> dict:
    """获取当前登录用户信息。"""
    if token is None:
        return build_error_response("未提供认证令牌")

    uid = auth_session.validate_token(token)
    if uid is None:
        return build_error_response("令牌无效或已过期")

    profile = get_user_by_uid(uid)
    if profile is None:
        return build_error_response("用户不存在")

    return {"ok": True, "message": "ok", "data": {"user": profile}}


@app.post("/api/auth/logout")
def logout(
    token: str | None = Header(default=None, alias="X-Paoqi-Auth-Token"),
) -> dict:
    """退出登录，撤销令牌。"""
    if token:
        auth_session.revoke_token(token)
    return {"ok": True, "message": "已退出登录", "data": None}


# -------------------- 用户 API 端点 --------------------


@app.get("/api/user/{uid}")
def get_user_profile(uid: int) -> dict:
    """获取指定用户的公开 profile。"""
    profile = get_user_by_uid(uid)
    if profile is None:
        return build_error_response("用户不存在")

    # 返回公开信息（不含敏感数据）
    return {
        "ok": True,
        "message": "ok",
        "data": {
            "user": {
                "uid": profile["uid"],
                "username": profile["username"],
                "role": profile["role"],
                "intro_letter": profile.get("intro_letter", ""),
                "registered_at": profile.get("registered_at", ""),
            },
        },
    }


@app.post("/api/user/update-profile")
def update_profile(
    req: UpdateProfileRequest,
    uid: int = Depends(require_auth),
) -> dict:
    """更新当前用户的介绍信。"""
    try:
        profile = update_user_profile(uid, req.intro_letter)
        return {
            "ok": True,
            "message": "个人信息已更新",
            "data": {"user": profile},
        }
    except ValueError as e:
        return build_error_response(str(e))


@app.post("/api/user/change-password")
def change_password(
    req: ChangePasswordRequest,
    uid: int = Depends(require_auth),
) -> dict:
    """修改当前用户的密码。"""
    try:
        success = change_user_password(uid, req.old_password, req.new_password)
    except ValueError as e:
        return build_error_response(str(e))

    if not success:
        return build_error_response("旧密码不正确")

    return {"ok": True, "message": "密码已修改", "data": None}


@app.get("/api/user/settings")
def get_settings(
    uid: int = Depends(require_auth),
) -> dict:
    """获取当前用户的设置。"""
    settings = get_user_settings(uid)
    return {"ok": True, "message": "ok", "data": {"settings": settings}}


@app.put("/api/user/settings")
def save_settings(
    req: UpdateSettingsRequest,
    uid: int = Depends(require_auth),
) -> dict:
    """保存当前用户的设置。"""
    save_user_settings(uid, req.settings)
    return {"ok": True, "message": "设置已保存", "data": None}
