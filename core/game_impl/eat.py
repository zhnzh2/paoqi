# core/game_impl/eat.py
"""吃子相关逻辑实现"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from core.board import Position
from core.cannon import detect_new_cannons
from core.models import Piece
from core.record import player_name

if TYPE_CHECKING:
    from core.game import Game


def is_capturable_impl(self: "Game", x: int, y: int, attacker_color: str) -> bool:
    target = self.board.get(x, y)

    if target is None:
        return False

    if target.color == attacker_color:
        return False

    region = self.get_local_region(x, y)

    friendly_count = 0
    friendly_total = 0
    enemy_total = 0

    for rx, ry in region:
        piece = self.board.get(rx, ry)
        if piece is None:
            continue

        if piece.color == attacker_color:
            friendly_count += 1
            friendly_total += piece.level
        else:
            enemy_total += piece.level

    # "己方棋子数不少于被吃棋子周围格子数的一半"
    if friendly_count * 2 < len(region) - 1:
        return False

    # "己方总等级严格大于对方"
    if friendly_total <= enemy_total:
        return False

    return True


def get_capturable_targets_impl(self: "Game", attacker_color: str) -> List[Position]:
    result: List[Position] = []

    for y in range(1, self.board.SIZE + 1):
        for x in range(1, self.board.SIZE + 1):
            if self.is_capturable(x, y, attacker_color):
                result.append((x, y))

    return result


def eat_target_by_index_impl(self: "Game", index: int) -> None:
    if self.phase != "eat":
        raise ValueError("当前不是吃子阶段，不能执行吃子。")

    targets = self.get_capturable_targets(self.current_player)

    if not (1 <= index <= len(targets)):
        raise ValueError("可吃目标编号无效。")

    self.push_undo_snapshot()
    self.clear_last_action_events()
    x, y = targets[index - 1]
    old_piece = self.board.get(x, y)

    if old_piece is None:
        raise ValueError("目标位置为空，无法吃子。")

    self.chain_pass_count = 0
    before_cannons = self.get_cannons_by_color(self.current_player)
    self.clear_last_change_reached()

    before_piece = self._serialize_piece_at(x, y)
    self.board.set(x, y, Piece(self.current_player, 1))
    self.mark_reached_level(x, y, self.current_player, 1)
    after_piece = self._serialize_piece_at(x, y)
    self.add_last_action_event(
        self._make_event(
            "capture",
            x=x,
            y=y,
            captured=before_piece,
            placed=after_piece,
            player=self.current_player,
        )
    )

    self.record_capture((x, y))
    self.debug(
        f"{player_name(self.current_player)}: 吃掉 ({x}, {y}) 的 {old_piece.short()}，并在原地放置1级棋子"
    )

    after_cannons = self.get_cannons_by_color(self.current_player)

    self.last_new_cannons = detect_new_cannons(before_cannons, after_cannons)
    self.assign_muzzles_for_new_cannons()
    for new_cannon in self.last_new_cannons:
        self.add_last_action_event(
            self._make_event(
                "new_cannon",
                cannon=self._serialize_cannon(new_cannon),
            )
        )

    self.waiting_new_pool_cannons = self.last_new_cannons.copy()

    if self.pending_muzzle_cannons:
        self.phase = "muzzle"
        self._record_phase_change_event()
    else:
        self.add_waiting_new_cannons_to_pool()
        self.phase = "fire"
        self._record_phase_change_event()

    self.advance_turn()
