# core/game_impl/report.py
"""报告/展示相关方法实现"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from core.record import (
    cannon_report,
    capturable_report,
    debug_text,
    fire_report_text,
    fireable_report,
    history_text,
    new_cannons_report,
    pending_muzzle_report,
    player_name,
)

if TYPE_CHECKING:
    from core.game import Game


def status_text_impl(self: "Game") -> str:
    color = self.current_player
    place_count = len(self.board.legal_place_positions(color))
    upgrade_count = len(self.board.legal_upgrade_positions(color))
    total_count = place_count + upgrade_count

    return (
        f"第 {self.turn_number} 回合 | 当前行动方：{player_name(color)} | 当前阶段：{self.phase_name()}\n"
        f"可操作总数：{total_count} | 其中可放置：{place_count} | 可升级：{upgrade_count}"
    )


def game_result_report_impl(self: "Game") -> str:
    red_score, blue_score = self.calculate_score()
    winner = self.determine_winner_by_score()

    reason_text_map = {
        "no_legal_move": f"{player_name(self.current_player)}无法进行合法落子",
        "agreement": "双方协商终局",
        "resign": f"{player_name(self.current_player)}投降",
    }
    reason_text = reason_text_map.get(self.game_over_reason, "游戏结束")

    lines: List[str] = []
    lines.append("游戏结束")
    lines.append(f"结束原因：{reason_text}")
    lines.append(f"红方棋子数：{red_score}")
    lines.append(f"蓝方棋子数：{blue_score}（已含 +9 补偿）")

    if winner is None:
        lines.append("结果：平局")
    else:
        lines.append(f"胜者：{player_name(winner)}")

    return "\n".join(lines)


def history_text_impl(self: "Game") -> str:
    return history_text(self.history)


def debug_text_impl(self: "Game") -> str:
    return debug_text(self.debug_log)


def fire_report_text_impl(self: "Game") -> str:
    return fire_report_text(self.last_fire_report_lines)


def new_cannons_report_impl(self: "Game") -> str:
    return new_cannons_report(self.last_new_cannons)


def cannon_report_impl(self: "Game") -> str:
    return cannon_report(
        self.get_cannons_by_color("R"),
        self.get_cannons_by_color("B"),
    )


def pending_muzzle_report_impl(self: "Game") -> str:
    return pending_muzzle_report(self.pending_muzzle_cannons)


def fireable_report_impl(self: "Game") -> str:
    return fireable_report(self.current_player, self.get_fireable_cannons())


def capturable_report_impl(self: "Game") -> str:
    return capturable_report(
        self.current_player,
        self.get_capturable_targets(self.current_player),
        self.board,
    )
