from __future__ import annotations

from core.game import Game

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
