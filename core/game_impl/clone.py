# core/game_impl/clone.py
"""Game.clone() 实现"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from core.board import Board
from core.models import Piece
from core.undo import copy_cannon

if TYPE_CHECKING:
    from core.game import Game


def clone_impl(self: "Game") -> "Game":
    from core.game import Game as GameClass

    cloned = GameClass.__new__(GameClass)
    # 深拷贝棋盘（避免共享引用）
    cloned.board = Board()
    cloned.board.grid = [
        [
            Piece(p.color, p.level) if p is not None else None
            for p in row
        ]
        for row in self.board.grid
    ]
    # 拷贝简单状态
    cloned.current_player = self.current_player
    cloned.turn_number = self.turn_number
    cloned.history = self.history.copy()
    cloned.debug_log = self.debug_log.copy()
    cloned.command_log = self.command_log.copy()
    cloned.undo_stack = []  # 克隆不需要撤销栈
    cloned.game_over = self.game_over
    cloned.winner = self.winner
    cloned.game_over_reason = self.game_over_reason
    cloned.cannon_record_style = self.cannon_record_style
    cloned.last_new_cannons = [copy_cannon(c) for c in self.last_new_cannons]
    cloned.pending_muzzle_cannons = [copy_cannon(c) for c in self.pending_muzzle_cannons]
    cloned.last_fire_report_lines = self.last_fire_report_lines.copy()
    cloned.auto_action_messages = self.auto_action_messages.copy()
    cloned.last_change_reached = self.last_change_reached.copy()
    cloned.last_action_events = deepcopy(self.last_action_events)
    cloned.cannon_mouth_map = self.cannon_mouth_map.copy()
    cloned.fire_cannon_pool = [copy_cannon(c) for c in self.fire_cannon_pool]
    cloned.waiting_new_pool_cannons = [copy_cannon(c) for c in self.waiting_new_pool_cannons]
    cloned.phase = self.phase
    cloned.round_drop_player = self.round_drop_player
    cloned.chain_pass_count = self.chain_pass_count
    cloned.pending_auto_action = deepcopy(self.pending_auto_action)
    cloned.pending_auto_message = self.pending_auto_message
    return cloned
