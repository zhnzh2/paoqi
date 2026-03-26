#state_codec.py
from __future__ import annotations

from typing import Any

from core.game import Game


def encode_board_numeric(game: Game) -> list[list[int]]:
    rows: list[list[int]] = []

    for y in range(1, 10):
        row: list[int] = []

        for x in range(1, 10):
            piece = game.board.get(x, y)

            if piece is None:
                row.append(0)
            elif piece.color == "R":
                row.append(piece.level)
            else:
                row.append(-piece.level)

        rows.append(row)

    return rows


def encode_board_compact(game: Game) -> list[list[str]]:
    rows: list[list[str]] = []

    for y in range(1, 10):
        row: list[str] = []

        for x in range(1, 10):
            piece = game.board.get(x, y)

            if piece is None:
                row.append(".")
            else:
                row.append(f"{piece.color}{piece.level}")

        rows.append(row)

    return rows


def encode_phase_one_hot(game: Game) -> dict[str, int]:
    phase = game.phase

    return {
        "is_drop": 1 if phase == "drop" else 0,
        "is_muzzle": 1 if phase == "muzzle" else 0,
        "is_fire": 1 if phase == "fire" else 0,
        "is_eat": 1 if phase == "eat" else 0,
    }


def encode_player_flag(game: Game) -> dict[str, int]:
    return {
        "current_player_is_red": 1 if game.current_player == "R" else 0,
        "current_player_is_blue": 1 if game.current_player == "B" else 0,
        "round_drop_player_is_red": 1 if game.round_drop_player == "R" else 0,
        "round_drop_player_is_blue": 1 if game.round_drop_player == "B" else 0,
    }


def encode_scalar_features(game: Game) -> dict[str, int]:
    red_score, blue_score = game.calculate_score()
    legal_actions = game.get_legal_actions()

    return {
        "turn_number": game.turn_number,
        "chain_pass_count": game.chain_pass_count,
        "game_over": 1 if game.game_over else 0,
        "winner_red": 1 if game.winner == "R" else 0,
        "winner_blue": 1 if game.winner == "B" else 0,
        "winner_none": 1 if game.winner is None else 0,
        "red_score": red_score,
        "blue_score": blue_score,
        "legal_action_count": len(legal_actions),
        "pending_muzzle_count": len(game.pending_muzzle_cannons),
        "fire_pool_count": len(game.fire_cannon_pool),
        "last_new_cannon_count": len(game.last_new_cannons),
    }


def encode_state(game: Game) -> dict[str, Any]:
    return {
        "board_numeric": encode_board_numeric(game),
        "board_compact": encode_board_compact(game),
        "phase": game.phase,
        "current_player": game.current_player,
        "round_drop_player": game.round_drop_player,
        "phase_one_hot": encode_phase_one_hot(game),
        "player_flags": encode_player_flag(game),
        "scalar_features": encode_scalar_features(game),
    }