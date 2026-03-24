#undo.py
from __future__ import annotations

from typing import List

from models import Piece, Cannon

def copy_board_grid(board_grid: list[list[Piece | None]]) -> list[list[Piece | None]]:
    copied: list[list[Piece | None]] = []

    for row in board_grid:
        new_row: list[Piece | None] = []
        for piece in row:
            if piece is None:
                new_row.append(None)
            else:
                new_row.append(Piece(piece.color, piece.level))
        copied.append(new_row)

    return copied


def copy_cannon(cannon: Cannon) -> Cannon:
    copied = Cannon(
        color=cannon.color,
        level=cannon.level,
        positions=tuple(cannon.positions),
        direction=cannon.direction,
    )
    copied.mouth = cannon.mouth
    return copied


def copy_cannon_list(cannons: List[Cannon]) -> List[Cannon]:
    return [copy_cannon(c) for c in cannons]

def snapshot_state(game) -> dict:
    return {
        "board_grid": copy_board_grid(game.board.grid),
        "current_player": game.current_player,
        "turn_number": game.turn_number,
        "history": game.history.copy(),
        "debug_log": game.debug_log.copy(),
        "command_log": game.command_log.copy(),
        "game_over": game.game_over,
        "winner": game.winner,
        "last_new_cannons": copy_cannon_list(game.last_new_cannons),
        "pending_muzzle_cannons": copy_cannon_list(game.pending_muzzle_cannons),
        "last_fire_report_lines": game.last_fire_report_lines.copy(),
        "last_change_reached": game.last_change_reached.copy(),
        "cannon_mouth_map": game.cannon_mouth_map.copy(),
        "fire_cannon_pool": copy_cannon_list(game.fire_cannon_pool),
        "waiting_new_pool_cannons": copy_cannon_list(game.waiting_new_pool_cannons),
        "phase": game.phase,
        "round_drop_player": game.round_drop_player,
        "chain_pass_count": game.chain_pass_count,
        "cannon_record_style": game.cannon_record_style,
    }


def restore_state(game, snapshot: dict) -> None:
    game.board.grid = snapshot["board_grid"]
    game.current_player = snapshot["current_player"]
    game.turn_number = snapshot["turn_number"]
    game.history = snapshot["history"]
    game.debug_log = snapshot["debug_log"]
    game.command_log = snapshot["command_log"]
    game.game_over = snapshot["game_over"]
    game.winner = snapshot["winner"]
    game.last_new_cannons = snapshot["last_new_cannons"]
    game.pending_muzzle_cannons = snapshot["pending_muzzle_cannons"]
    game.last_fire_report_lines = snapshot["last_fire_report_lines"]
    game.last_change_reached = snapshot["last_change_reached"]
    game.cannon_mouth_map = snapshot["cannon_mouth_map"]
    game.fire_cannon_pool = snapshot["fire_cannon_pool"]
    game.waiting_new_pool_cannons = snapshot["waiting_new_pool_cannons"]
    game.phase = snapshot["phase"]
    game.round_drop_player = snapshot["round_drop_player"]
    game.chain_pass_count = snapshot["chain_pass_count"]
    game.cannon_record_style = snapshot["cannon_record_style"]