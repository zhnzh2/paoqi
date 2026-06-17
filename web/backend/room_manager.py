"""房间管理器 —— 管理联机对战的房间生命周期。

每个 Room 持有一个权威 Game 实例，通过 WebSocket 同步状态。
先进入者为红方，后进入者为蓝方。
"""

from __future__ import annotations

import random
import string
import time
from typing import Any

from core.game import Game
from fastapi import WebSocket

ROOM_CODE_CHARS = string.ascii_uppercase + string.digits  # A-Z, 0-9
ROOM_CODE_LENGTH = 6


class Room:
    """一个联机对局房间。"""

    def __init__(self, code: str, red_uid: int, red_username: str):
        self.code = code
        self.game = Game()
        self.red_uid = red_uid
        self.red_username = red_username
        self.blue_uid: int | None = None
        self.blue_username: str | None = None
        self.red_ws: WebSocket | None = None
        self.blue_ws: WebSocket | None = None
        self.red_connected = False
        self.blue_connected = False
        self.created_at = time.time()

    @property
    def is_full(self) -> bool:
        return self.blue_uid is not None

    @property
    def player_count(self) -> int:
        return 1 + (1 if self.blue_uid else 0)

    def get_color(self, uid: int) -> str | None:
        if uid == self.red_uid:
            return "R"
        if uid == self.blue_uid:
            return "B"
        return None

    def get_ws(self, uid: int) -> WebSocket | None:
        if uid == self.red_uid:
            return self.red_ws
        if uid == self.blue_uid:
            return self.blue_ws
        return None

    def set_ws(self, uid: int, ws: WebSocket) -> None:
        if uid == self.red_uid:
            self.red_ws = ws
            self.red_connected = True
        elif uid == self.blue_uid:
            self.blue_ws = ws
            self.blue_connected = True

    def mark_disconnected(self, uid: int) -> None:
        if uid == self.red_uid:
            self.red_connected = False
        elif uid == self.blue_uid:
            self.red_connected = False
            self.blue_connected = False

    def get_players_info(self) -> list[dict[str, Any]]:
        players = [
            {"uid": self.red_uid, "username": self.red_username, "color": "R",
             "connected": self.red_connected},
        ]
        if self.blue_uid is not None:
            players.append(
                {"uid": self.blue_uid, "username": self.blue_username, "color": "B",
                 "connected": self.blue_connected},
            )
        return players


class RoomManager:
    """单例房间管理器。"""

    def __init__(self):
        self._rooms: dict[str, Room] = {}
        self._uid_to_code: dict[int, str] = {}

    # ------------------------------------------------------------------
    # 房间码生成
    # ------------------------------------------------------------------

    def _generate_code(self) -> str:
        while True:
            code = "".join(random.choices(ROOM_CODE_CHARS, k=ROOM_CODE_LENGTH))
            if code not in self._rooms:
                return code

    # ------------------------------------------------------------------
    # 创建 / 加入 / 离开
    # ------------------------------------------------------------------

    def create_room(self, uid: int, username: str) -> str:
        """创建一个新房间，返回房间码。若用户已在其他房间则先离开。"""
        self._leave_current_room(uid)
        code = self._generate_code()
        self._rooms[code] = Room(code, uid, username)
        self._uid_to_code[uid] = code
        return code

    def join_room(self, code: str, uid: int, username: str) -> Room:
        """加入已有房间。返回 Room；失败抛出 ValueError。"""
        room = self._rooms.get(code)
        if room is None:
            raise ValueError("房间不存在")
        if room.blue_uid is not None:
            raise ValueError("房间已满")
        if uid == room.red_uid:
            # 自己创建的房间，不用重复加入，直接返回
            return room
        self._leave_current_room(uid)
        room.blue_uid = uid
        room.blue_username = username
        self._uid_to_code[uid] = code
        return room

    def leave_room(self, code: str, uid: int) -> None:
        """玩家离开房间。若房间为空则删除。"""
        room = self._rooms.get(code)
        if room is None:
            return
        if uid == room.red_uid:
            room.red_uid = -1  # 标记红方已离开
            room.red_connected = False
            room.red_ws = None
        elif uid == room.blue_uid:
            room.blue_uid = -1  # 标记蓝方已离开
            room.blue_connected = False
            room.blue_ws = None
        self._uid_to_code.pop(uid, None)

        # 双方都离开则清理房间
        if room.red_uid == -1 and room.blue_uid in (None, -1):
            self._rooms.pop(code, None)

    def _leave_current_room(self, uid: int) -> None:
        """用户加入新房间前，从旧房间退出。"""
        existing_code = self._uid_to_code.get(uid)
        if existing_code:
            self.leave_room(existing_code, uid)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def get_room(self, code: str) -> Room | None:
        return self._rooms.get(code)

    def get_room_by_uid(self, uid: int) -> Room | None:
        code = self._uid_to_code.get(uid)
        if code:
            return self._rooms.get(code)
        return None

    def list_rooms(self) -> list[dict[str, Any]]:
        """返回可加入房间的公开信息列表。"""
        return [
            {
                "code": r.code,
                "player_count": r.player_count,
                "game_started": r.is_full,
                "red_username": r.red_username,
                "created_at": r.created_at,
            }
            for r in self._rooms.values()
        ]
