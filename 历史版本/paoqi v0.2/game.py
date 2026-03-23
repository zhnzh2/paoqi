from __future__ import annotations

from typing import List, Tuple

from board import Board, Position
from models import Piece, Cannon
from cannon import find_all_cannons, find_cannons_by_color


class Game:
    def __init__(self) -> None:
        self.board = Board()
        self.board.setup_initial()
        self.current_player = "R"  # 红先
        self.turn_number = 1
        self.history: List[str] = []
        self.game_over = False
        self.winner: str | None = None
        self.last_new_cannons: List[Cannon] = []

    def player_name(self, color: str) -> str:
        return "红方" if color == "R" else "蓝方"

    def opponent(self, color: str) -> str:
        return "B" if color == "R" else "R"

    def legal_place_positions(self, color: str) -> List[Position]:
        result: List[Position] = []
        for y in range(1, self.board.SIZE + 1):
            for x in range(1, self.board.SIZE + 1):
                if self.board.is_empty(x, y) and self.board.has_adjacent_friendly(x, y, color):
                    result.append((x, y))
        return result

    def legal_upgrade_positions(self, color: str) -> List[Position]:
        result: List[Position] = []
        for y in range(1, self.board.SIZE + 1):
            for x in range(1, self.board.SIZE + 1):
                piece = self.board.get(x, y)
                if piece is not None and piece.color == color and piece.level in (1, 2):
                    result.append((x, y))
        return result

    def all_legal_moves(self, color: str) -> List[str]:
        moves: List[str] = []
        for x, y in self.legal_place_positions(color):
            moves.append(f"move {x} {y}   [放置]")
        for x, y in self.legal_upgrade_positions(color):
            piece = self.board.get(x, y)
            if piece is not None:
                moves.append(f"move {x} {y}   [升级到{piece.level + 1}级]")
        return moves

    def can_player_move(self, color: str) -> bool:
        return bool(self.legal_place_positions(color) or self.legal_upgrade_positions(color))

    def check_game_over_at_turn_start(self) -> bool:
        if not self.can_player_move(self.current_player):
            self.game_over = True
            self.winner = self.opponent(self.current_player)
            return True
        return False

    def apply_place(self, x: int, y: int) -> None:
        color = self.current_player
        if not self.board.in_bounds(x, y):
            raise ValueError("坐标越界。")
        if not self.board.is_empty(x, y):
            raise ValueError("该位置不是空格，不能放置。")
        if not self.board.has_adjacent_friendly(x, y, color):
            raise ValueError("该空格不能落子：必须与至少一枚己方棋子边相邻。")

        self.board.set(x, y, Piece(color, 1))
        self.history.append(f"{self.player_name(color)}: 在 ({x}, {y}) 放置1级棋子")

    def apply_upgrade(self, x: int, y: int) -> None:
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
        self.history.append(
            f"{self.player_name(color)}: 将 ({x}, {y}) 从{old_level}级升级到{piece.level}级"
        )

    def apply_move(self, x: int, y: int) -> None:
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

    def apply_command(self, command: str) -> None:
        parts = command.strip().split()
        if len(parts) != 3:
            raise ValueError("命令格式错误。请使用：move x y")

        action = parts[0].lower()
        if action != "move":
            raise ValueError("未知命令。当前只支持：move x y")

        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError as exc:
            raise ValueError("x 和 y 必须是整数。") from exc

        before_cannons = self.get_all_cannons()
        self.apply_move(x, y)
        after_cannons = self.get_all_cannons()

        self.last_new_cannons = self.detect_new_cannons(before_cannons, after_cannons)

    def end_turn(self) -> None:
        self.current_player = self.opponent(self.current_player)
        self.turn_number += 1

    def status_text(self) -> str:
        color = self.current_player
        place_count = len(self.legal_place_positions(color))
        upgrade_count = len(self.legal_upgrade_positions(color))
        total_count = place_count + upgrade_count
        return (
            f"第 {self.turn_number} 回合 | 当前行动方：{self.player_name(color)}\n"
            f"可操作总数：{total_count} | 其中可放置：{place_count} | 可升级：{upgrade_count}"
        )
    def get_all_cannons(self) -> List[Cannon]:
        return find_all_cannons(self.board)
    def cannon_signature(self, cannon: Cannon) -> tuple:
        return (
            cannon.color,
            cannon.level,
            cannon.positions,
            cannon.direction,
        )
    def detect_new_cannons(
        self,
        before_cannons: List[Cannon],
        after_cannons: List[Cannon],
    ) -> List[Cannon]:
        before_set = {self.cannon_signature(c) for c in before_cannons}
        new_cannons: List[Cannon] = []

        for cannon in after_cannons:
            if self.cannon_signature(cannon) not in before_set:
                new_cannons.append(cannon)

        return new_cannons
    def new_cannons_report(self) -> str:
        if not self.last_new_cannons:
            return "本步未形成新炮。"

        lines: List[str] = ["新形成炮管："]
        for cannon in self.last_new_cannons:
            color_name = self.player_name(cannon.color)
            lines.append(f"  {color_name} {cannon.short()}")
        return "\n".join(lines)
    def get_cannons_by_color(self, color: str) -> List[Cannon]:
        return find_cannons_by_color(self.board, color)
    def cannon_report(self) -> str:
        red_cannons = self.get_cannons_by_color("R")
        blue_cannons = self.get_cannons_by_color("B")

        lines: List[str] = []

        lines.append("红方炮管：")
        if not red_cannons:
            lines.append("  （暂无）")
        else:
            for i, cannon in enumerate(red_cannons, start=1):
                lines.append(f"  {i}. {cannon.short()}")

        lines.append("")

        lines.append("蓝方炮管：")
        if not blue_cannons:
            lines.append("  （暂无）")
        else:
            for i, cannon in enumerate(blue_cannons, start=1):
                lines.append(f"  {i}. {cannon.short()}")

        return "\n".join(lines)