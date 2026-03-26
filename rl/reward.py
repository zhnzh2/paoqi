#reward.py
from __future__ import annotations

from core.game import Game


def get_terminal_reward(game: Game, perspective: str) -> float:
    winner = game.get_winner()

    if winner == perspective:
        return 1.0

    if winner is None:
        return 0.0

    return -1.0


def get_step_reward(game: Game, acting_player: str) -> float:
    if not game.is_terminal():
        return 0.0

    return get_terminal_reward(game, acting_player)