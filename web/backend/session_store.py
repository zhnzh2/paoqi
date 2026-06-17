from __future__ import annotations

import uuid

from core.game import Game


class AuthSession:
    """基于内存的认证令牌存储 —— token 到 uid 的映射。"""

    def __init__(self) -> None:
        self._tokens: dict[str, int] = {}

    def create_token(self, uid: int) -> str:
        """为用户创建一个新的认证令牌。"""
        token = str(uuid.uuid4())
        self._tokens[token] = uid
        return token

    def validate_token(self, token: str) -> int | None:
        """验证令牌，返回对应的 uid 或 None。"""
        return self._tokens.get(token)

    def revoke_token(self, token: str) -> None:
        """撤销令牌。"""
        self._tokens.pop(token, None)


class LocalGameSession:
    DEFAULT_SESSION_ID = "default"

    def __init__(self) -> None:
        self.games: dict[str, Game] = {
            self.DEFAULT_SESSION_ID: Game(),
        }

    def _normalize_session_id(self, session_id: str | None) -> str:
        if not session_id:
            return self.DEFAULT_SESSION_ID
        return session_id.strip() or self.DEFAULT_SESSION_ID

    def reset(self, session_id: str | None = None) -> Game:
        key = self._normalize_session_id(session_id)
        self.games[key] = Game()
        return self.games[key]

    def get_game(self, session_id: str | None = None) -> Game:
        key = self._normalize_session_id(session_id)
        if key not in self.games:
            self.games[key] = Game()
        return self.games[key]

    def set_game(self, game: Game, session_id: str | None = None) -> None:
        key = self._normalize_session_id(session_id)
        self.games[key] = game
