#resolution.py
from __future__ import annotations

from typing import Dict, List

from board import Board, Position
from models import Cannon, Piece
from cannon import front_positions, cannon_positions_from_mouth

def signed_value(piece: Piece | None, firing_color: str) -> int:
    if piece is None:
        return 0

    if piece.color == firing_color:
        return piece.level

    return -piece.level


def piece_from_signed_value(
    value: int,
    firing_color: str,
    opponent_color: str,
) -> Piece | None:
    if value == 0:
        return None

    level = min(5, abs(value))

    if value > 0:
        return Piece(firing_color, level)

    return Piece(opponent_color, level)

def collect_front_updates(
    board: Board,
    cannon: Cannon,
    firing_color: str,
    opponent_color: str,
) -> Dict[Position, Piece | None]:
    updates: Dict[Position, Piece | None] = {}

    for pos in front_positions(board, cannon):
        x, y = pos
        old_piece = board.get(x, y)
        old_value = signed_value(old_piece, firing_color)
        new_value = old_value + cannon.level
        new_piece = piece_from_signed_value(new_value, firing_color, opponent_color)
        updates[pos] = new_piece

    return updates

def apply_piece_updates(
    board: Board,
    updates: Dict[Position, Piece | None],
) -> None:
    for (x, y), piece in updates.items():
        board.set(x, y, piece)

def collect_body_updates(
    board: Board,
    cannon: Cannon,
) -> Dict[Position, Piece | None]:
    updates: Dict[Position, Piece | None] = {}

    positions_from_mouth = cannon_positions_from_mouth(cannon)

    for distance, (x, y) in enumerate(positions_from_mouth):
        if distance % 2 != 1:
            continue

        piece = board.get(x, y)

        if piece is None:
            continue

        if piece.color != cannon.color:
            continue

        new_level = min(5, piece.level + 1)
        updates[(x, y)] = Piece(piece.color, new_level)

    return updates

def merge_reached_from_updates(
    reached: Dict[Position, tuple[str, int]],
    updates: Dict[Position, Piece | None],
) -> None:
    for pos, piece in updates.items():
        if piece is not None:
            reached[pos] = (piece.color, piece.level)