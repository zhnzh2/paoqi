from __future__ import annotations

from core.game import Game


class LocalGameSession:
    def __init__(self) -> None:
        self.game = Game()

    def reset(self) -> Game:
        self.game = Game()
        return self.game

    def get_game(self) -> Game:
        return self.game

    def set_game(self, game: Game) -> None:
        self.game = game