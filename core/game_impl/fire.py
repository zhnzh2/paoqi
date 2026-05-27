# core/game_impl/fire.py
"""fire_cannon_by_index 的打炮逻辑实现"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from core.cannon import detect_new_cannons, front_positions
from core.models import Cannon
from core.record import piece_text, player_name
from core.resolution import (
    apply_piece_updates,
    collect_body_updates,
    collect_front_updates,
    merge_reached_from_updates,
)

if TYPE_CHECKING:
    from core.game import Game


def fire_cannon_by_index_impl(self: "Game", index: int) -> None:
    if self.phase != "fire":
        raise ValueError("当前不是打炮阶段，不能发炮。")

    if not (1 <= index <= len(self.fire_cannon_pool)):
        raise ValueError("可发射炮编号无效。")

    self.push_undo_snapshot()
    self.clear_last_action_events()
    cannon = self.fire_cannon_pool.pop(index - 1)
    firing_color = self.current_player
    self.add_last_action_event(
        self._make_event(
            "fire",
            index=index,
            cannon=self._serialize_cannon(cannon),
            player=firing_color,
        )
    )
    self.chain_pass_count = 0

    before_cannons = self.get_cannons_by_color(self.current_player)
    self.clear_last_change_reached()
    self.last_fire_report_lines = []

    self.last_fire_report_lines.append("本次发炮明细：")
    self.last_fire_report_lines.append(
        f"  发射炮管：{player_name(firing_color)} {cannon.short()}"
    )

    # 1. 前方攻击：基于发射前棋盘记录变化
    front_targets = front_positions(self.board, cannon)
    front_report_lines: List[str] = []

    if front_targets:
        self.last_fire_report_lines.append("  前方作用格：")
    else:
        self.last_fire_report_lines.append("  前方作用格：无")

    front_updates_map = collect_front_updates(
        self.board,
        cannon,
        firing_color,
        self.opponent(firing_color),
    )

    for pos in front_targets:
        x, y = pos
        old_piece = self.board.get(x, y)
        new_piece = front_updates_map[pos]

        front_report_lines.append(
            f"    ({x}, {y}): {piece_text(old_piece)} -> {piece_text(new_piece)}"
        )

    self.last_fire_report_lines.extend(front_report_lines)

    # 2. 炮体内部升级：距炮口奇数距离的棋子 +1
    body_updates_map = collect_body_updates(self.board, cannon)
    body_upgrade_lines: List[str] = []

    for (x, y), new_piece in body_updates_map.items():
        old_piece = self.board.get(x, y)

        body_upgrade_lines.append(
            f"    ({x}, {y}): {piece_text(old_piece)} -> {piece_text(new_piece)}"
        )

    if body_upgrade_lines:
        self.last_fire_report_lines.append("  炮体内部升级：")
        self.last_fire_report_lines.extend(body_upgrade_lines)
    else:
        self.last_fire_report_lines.append("  炮体内部升级：无")

    # 3. 统一写回前方攻击结果，并记录本次变化达到的等级
    for (x, y), new_piece in front_updates_map.items():
        old_piece = self.board.get(x, y)
        self.add_last_action_event(
            self._make_piece_change_event(
                x=x,
                y=y,
                before_piece=(
                    None
                    if old_piece is None
                    else {
                        "color": old_piece.color,
                        "level": old_piece.level,
                        "short": old_piece.short(),
                    }
                ),
                after_piece=(
                    None
                    if new_piece is None
                    else {
                        "color": new_piece.color,
                        "level": new_piece.level,
                        "short": new_piece.short(),
                    }
                ),
                reason="front_attack",
            )
        )
    apply_piece_updates(self.board, front_updates_map)
    merge_reached_from_updates(self.last_change_reached, front_updates_map)

    # 4. 统一写回炮体内部升级结果，并记录本次变化达到的等级
    for (x, y), new_piece in body_updates_map.items():
        old_piece = self.board.get(x, y)
        self.add_last_action_event(
            self._make_piece_change_event(
                x=x,
                y=y,
                before_piece=(
                    None
                    if old_piece is None
                    else {
                        "color": old_piece.color,
                        "level": old_piece.level,
                        "short": old_piece.short(),
                    }
                ),
                after_piece=(
                    None
                    if new_piece is None
                    else {
                        "color": new_piece.color,
                        "level": new_piece.level,
                        "short": new_piece.short(),
                    }
                ),
                reason="body_upgrade",
            )
        )
    apply_piece_updates(self.board, body_updates_map)
    merge_reached_from_updates(self.last_change_reached, body_updates_map)

    self.record_fire(cannon)

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

    if self.last_new_cannons:
        self.last_fire_report_lines.append("  新形成炮管：")
        for new_cannon in self.last_new_cannons:
            self.last_fire_report_lines.append(
                f"    {player_name(new_cannon.color)} {new_cannon.short()}"
            )
    else:
        self.last_fire_report_lines.append("  新形成炮管：无")

    self.waiting_new_pool_cannons = self.last_new_cannons.copy()

    if self.pending_muzzle_cannons:
        self.phase = "muzzle"
        self._record_phase_change_event()
    else:
        self.add_waiting_new_cannons_to_pool()

        # 如果当前方仍然还有可发射炮，就继续留在打炮阶段
        if self.fire_cannon_pool:
            self.phase = "fire"
            self._record_phase_change_event()
        else:
            self.phase = "eat"
            self._record_phase_change_event()

    self.advance_turn()
