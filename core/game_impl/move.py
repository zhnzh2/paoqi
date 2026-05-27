# core/game_impl/move.py
"""落子/放置/升级的底层实现"""
from __future__ import annotations

from typing import TYPE_CHECKING

from core.models import Piece
from core.record import player_name

if TYPE_CHECKING:
    from core.game import Game


def apply_place_impl(self: "Game", x: int, y: int) -> None:
    color = self.current_player

    if not self.board.in_bounds(x, y):
        raise ValueError("坐标越界。")
    if not self.board.is_empty(x, y):
        raise ValueError("该位置不是空格，不能放置。")
    if not self.board.has_adjacent_friendly(x, y, color):
        raise ValueError("该空格不能落子：必须与至少一枚己方棋子边相邻。")

    self.board.set(x, y, Piece(color, 1))
    self.mark_reached_level(x, y, color, 1)
    self.record(f"{player_name(color)}在({x}, {y})落子")


def apply_upgrade_impl(self: "Game", x: int, y: int) -> None:
    color = self.current_player

    if not self.board.in_bounds(x, y):
        raise ValueError("坐标越界。")

    piece = self.board.get(x, y)
    if piece is None:
        raise ValueError("该位置没有棋子，不能升级。")
    if piece.color != color:
        raise ValueError("只能升级己方棋子。")
    if piece.level not in (1, 2):
        raise ValueError("落子阶段只允许把1级升到2级，或把2级升到3级。")

    old_level = piece.level
    piece.level += 1
    self.mark_reached_level(x, y, color, piece.level)

    self.debug(
        f"{player_name(color)}: 将 ({x}, {y}) 从{old_level}级升级到{piece.level}级"
    )
    self.record(f"{player_name(color)}在({x}, {y})落子")


def apply_move_impl(self: "Game", x: int, y: int) -> None:
    if not self.board.in_bounds(x, y):
        raise ValueError("坐标越界。")

    piece = self.board.get(x, y)

    if piece is None:
        self.apply_place(x, y)
        return

    if piece.color != self.current_player:
        raise ValueError("该位置有敌方棋子，不能操作。")

    if piece.level in (1, 2):
        self.apply_upgrade(x, y)
        return

    raise ValueError("该位置已有己方3级及以上棋子，落子阶段不能继续升级。")
