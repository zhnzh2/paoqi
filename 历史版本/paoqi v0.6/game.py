from __future__ import annotations

from typing import List

from board import Board, Position
from models import Piece, Cannon
from cannon import find_all_cannons

class Game:
    def __init__(self) -> None:
        self.board = Board()
        self.board.setup_initial()

        self.current_player = "R"   # 红先
        self.turn_number = 1

        self.history: List[str] = []
        self.game_over = False
        self.winner: str | None = None

        self.last_new_cannons: List[Cannon] = []
        self.pending_muzzle_cannons: List[Cannon] = []
        self.last_fire_report_lines: List[str] = []
        self.last_change_reached: dict[Position, tuple[str, int]] = {}

        # 记录“这门炮”的炮口方向
        self.cannon_mouth_map: dict[tuple, str] = {}

        # 当前打炮阶段冻结的炮管集合
        self.fire_cannon_pool: List[Cannon] = []

        # 待加入炮管集合的新炮（等炮口选完后加入）
        self.waiting_new_pool_cannons: List[Cannon] = []
        
        # 当前阶段：
        # "drop"   = 落子阶段
        # "muzzle" = 有新炮，待选炮口
        # "fire"   = 打炮阶段
        self.phase = "drop"

        # 本次大回合的落子发起方
        self.round_drop_player: str | None = None

        # 连续“无法继续结算”的方数
        self.chain_pass_count = 0

    def player_name(self, color: str) -> str:
        return "红方" if color == "R" else "蓝方"

    def opponent(self, color: str) -> str:
        return "B" if color == "R" else "R"

    def mark_reached_level(self, x: int, y: int, color: str, level: int) -> None:
        self.last_change_reached[(x, y)] = (color, level)

    def clear_last_change_reached(self) -> None:
        self.last_change_reached = {}

    def phase_name(self) -> str:
        if self.phase == "drop":
            return "落子阶段"
        if self.phase == "muzzle":
            return "炮口选择阶段"
        if self.phase == "fire":
            return "打炮阶段"
        return "吃子阶段"

    #扫描这一方当前所有炮，已有炮口的直接进 fire_cannon_pool
    #没有炮口的尝试自动判，自动判不了的进 pending_muzzle_cannons
    #然后进入 muzzle 或 fire
    def start_resolution_for_current_player(self) -> None:
        self.fire_cannon_pool = []
        self.pending_muzzle_cannons = []
        self.waiting_new_pool_cannons = []

        cannons = self.get_cannons_by_color(self.current_player)

        for cannon in cannons:
            if cannon.mouth is None:
                mouth = self.auto_determine_mouth(cannon)
                if mouth is None:
                    self.pending_muzzle_cannons.append(cannon)
                    self.waiting_new_pool_cannons.append(cannon)
                else:
                    cannon.mouth = mouth
                    self.cannon_mouth_map[self.cannon_signature(cannon)] = mouth

            if cannon.mouth is not None:
                self.fire_cannon_pool.append(cannon)

        if self.pending_muzzle_cannons:
            self.phase = "muzzle"
        else:
            self.phase = "fire"

    def has_pending_muzzle_choice(self) -> bool:
        return bool(self.pending_muzzle_cannons)

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

    # 游戏结束检查：当前阶段是落子阶段，且当前玩家无任何合法落子/升级位置
    def check_game_over_at_turn_start(self) -> bool:
        if self.phase != "drop":
            return False

        if self.game_over:
            return True

        if not self.can_player_move(self.current_player):
            self.game_over = True
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
        self.mark_reached_level(x, y, color, 1)
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
        self.mark_reached_level(x, y, color, piece.level)

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

    def cannon_signature(self, cannon: Cannon) -> tuple:
        return (
            cannon.color,
            cannon.level,
            cannon.positions,
            cannon.direction,
        )

    def cannon_contains(self, outer: Cannon, inner: Cannon) -> bool:
        if outer.color != inner.color:
            return False

        if outer.level != inner.level:
            return False

        if outer.direction != inner.direction:
            return False

        outer_set = set(outer.positions)
        inner_set = set(inner.positions)

        return inner_set.issubset(outer_set)

    def remove_contained_old_cannons(self, new_cannon: Cannon) -> None:
        remaining: List[Cannon] = []

        for old_cannon in self.fire_cannon_pool:
            if self.cannon_contains(new_cannon, old_cannon):
                self.history.append(
                    f"炮管集合更新: 新炮 {new_cannon.positions} 包含旧炮 {old_cannon.positions}，旧炮移出集合"
                )
            else:
                remaining.append(old_cannon)

        self.fire_cannon_pool = remaining

    def get_all_cannons(self) -> List[Cannon]:
        cannons = find_all_cannons(self.board)

        for cannon in cannons:
            self._apply_saved_mouth_to_cannon(cannon)

        return cannons

    def _apply_saved_mouth_to_cannon(self, cannon: Cannon) -> Cannon:
        sig = self.cannon_signature(cannon)

        if sig in self.cannon_mouth_map:
            cannon.mouth = self.cannon_mouth_map[sig]
            return cannon

        for pending in self.pending_muzzle_cannons:
            if self.cannon_signature(pending) == sig and pending.mouth is not None:
                cannon.mouth = pending.mouth
                return cannon

        return cannon
    
    # 旧版初始化函数，当前版本暂未使用
    def initialize_fire_cannon_pool(self) -> None:
        self.fire_cannon_pool = []

        for cannon in self.get_cannons_by_color(self.current_player):
            if cannon.mouth is not None:
                self.fire_cannon_pool.append(cannon)

    def get_cannons_by_color(self, color: str) -> List[Cannon]:
        return [c for c in self.get_all_cannons() if c.color == color]

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

    def auto_determine_mouth(self, cannon: Cannon) -> str | None:
        candidates: List[Position] = []

        for pos, (color, level) in self.last_change_reached.items():
            if color == cannon.color and level == cannon.level and pos in cannon.positions:
                candidates.append(pos)

        if not candidates:
            return None

        if len(candidates) == 1:
            cx, cy = candidates[0]
        else:
            cx = sum(x for x, _ in candidates) / len(candidates)
            cy = sum(y for _, y in candidates) / len(candidates)

        end1 = cannon.positions[0]
        end2 = cannon.positions[-1]

        x1, y1 = end1
        x2, y2 = end2

        d1 = (cx - x1) ** 2 + (cy - y1) ** 2
        d2 = (cx - x2) ** 2 + (cy - y2) ** 2

        if d1 < d2:
            if cannon.direction == "H":
                return "L"
            return "U"

        if d2 < d1:
            if cannon.direction == "H":
                return "R"
            return "D"

        return None

    def assign_muzzles_for_new_cannons(self) -> None:
        self.pending_muzzle_cannons = []

        for cannon in self.last_new_cannons:
            mouth = self.auto_determine_mouth(cannon)

            if mouth is None:
                self.pending_muzzle_cannons.append(cannon)
            else:
                cannon.mouth = mouth
                self.cannon_mouth_map[self.cannon_signature(cannon)] = mouth
                self.history.append(
                    f"{self.player_name(cannon.color)}: 新炮 {cannon.positions} 自动判定炮口为 {mouth}"
                )

    def new_cannons_report(self) -> str:
        if not self.last_new_cannons:
            return "本步未形成新炮。"

        lines: List[str] = ["新形成炮管："]

        for cannon in self.last_new_cannons:
            lines.append(f"  {self.player_name(cannon.color)} {cannon.short()}")

        return "\n".join(lines)

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

    def pending_muzzle_report(self) -> str:
        if not self.pending_muzzle_cannons:
            return "当前没有待选择炮口的新炮。"

        lines: List[str] = ["请为新炮选择炮口方向："]

        for i, cannon in enumerate(self.pending_muzzle_cannons, start=1):
            if cannon.direction == "H":
                hint = "left / right"
            else:
                hint = "up / down"

            lines.append(
                f"  {i}. {self.player_name(cannon.color)} {cannon.short()}  -> 可选: {hint}"
            )

        return "\n".join(lines)

    def add_waiting_new_cannons_to_pool(self) -> None:
        if not self.waiting_new_pool_cannons:
            return

        for cannon in self.waiting_new_pool_cannons:
            self._apply_saved_mouth_to_cannon(cannon)

            # 先移除被新炮完全包含的旧炮
            self.remove_contained_old_cannons(cannon)

            sig = self.cannon_signature(cannon)
            exists = any(self.cannon_signature(old) == sig for old in self.fire_cannon_pool)

            if not exists:
                self.fire_cannon_pool.append(cannon)
                self.history.append(
                    f"炮管集合更新: 新炮 {cannon.positions} 加入当前炮管集合"
                )

        self.waiting_new_pool_cannons = []

    def set_cannon_mouth(self, index: int, direction_text: str) -> None:
        if not (1 <= index <= len(self.pending_muzzle_cannons)):
            raise ValueError("新炮编号无效。")

        cannon = self.pending_muzzle_cannons[index - 1]
        text = direction_text.lower()

        if cannon.direction == "H":
            if text == "left":
                mouth = "L"
            elif text == "right":
                mouth = "R"
            else:
                raise ValueError("横向炮只能选择 left 或 right。")
        else:
            if text == "up":
                mouth = "U"
            elif text == "down":
                mouth = "D"
            else:
                raise ValueError("纵向炮只能选择 up 或 down。")

        cannon.mouth = mouth
        self.cannon_mouth_map[self.cannon_signature(cannon)] = mouth

        # 关键：顺手把 last_new_cannons 里对应对象也同步一下
        for new_cannon in self.last_new_cannons:
            if self.cannon_signature(new_cannon) == self.cannon_signature(cannon):
                new_cannon.mouth = mouth

        self.history.append(
            f"{self.player_name(cannon.color)}: 为新炮 {cannon.positions} 指定炮口方向 {direction_text}"
        )

    def all_pending_muzzles_set(self) -> bool:
        return all(c.mouth is not None for c in self.pending_muzzle_cannons)

    def clear_pending_muzzles(self) -> None:
        self.pending_muzzle_cannons = []
        self.last_new_cannons = []

    def apply_command(self, command: str) -> None:
        if self.phase != "drop":
            raise ValueError("当前阶段不是落子阶段，无法执行该操作。")

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

        self.clear_last_change_reached()

        # 记录这次大回合的落子发起方
        self.round_drop_player = self.current_player
        self.chain_pass_count = 0

        before_cannons = self.get_cannons_by_color(self.current_player)
        self.apply_move(x, y)
        after_cannons = self.get_cannons_by_color(self.current_player)

        self.last_new_cannons = self.detect_new_cannons(before_cannons, after_cannons)
        self.assign_muzzles_for_new_cannons()

        self.waiting_new_pool_cannons = self.last_new_cannons.copy()

        if self.pending_muzzle_cannons:
            self.phase = "muzzle"
        else:
            self.add_waiting_new_cannons_to_pool()
            self.phase = "fire"

        self.advance_turn()

    def get_phase_relevant_cannons(self) -> List[Cannon]:
        return self.get_cannons_by_color(self.current_player)

    def get_fireable_cannons(self) -> List[Cannon]:
        return self.fire_cannon_pool.copy()

    def fireable_report(self) -> str:
        cannons = self.get_fireable_cannons()

        lines: List[str] = []
        lines.append(f"{self.player_name(self.current_player)} 当前可发射炮管：")

        if not cannons:
            lines.append("  （暂无）")
        else:
            for i, cannon in enumerate(cannons, start=1):
                lines.append(f"  {i}. {cannon.short()}")

        return "\n".join(lines)

    def _cannon_positions_from_mouth(self, cannon: Cannon) -> List[Position]:
        positions = list(cannon.positions)

        if cannon.mouth in ("R", "D"):
            positions.reverse()

        return positions

    def _front_positions(self, cannon: Cannon) -> List[Position]:
        n = cannon.length
        distance = n - 2
        positions_from_mouth = self._cannon_positions_from_mouth(cannon)

        mouth_x, mouth_y = positions_from_mouth[0]
        result: List[Position] = []

        if distance <= 0:
            return result

        if cannon.mouth == "L":
            for step in range(1, distance + 1):
                x = mouth_x - step
                y = mouth_y
                if self.board.in_bounds(x, y):
                    result.append((x, y))

        elif cannon.mouth == "R":
            for step in range(1, distance + 1):
                x = mouth_x + step
                y = mouth_y
                if self.board.in_bounds(x, y):
                    result.append((x, y))

        elif cannon.mouth == "U":
            for step in range(1, distance + 1):
                x = mouth_x
                y = mouth_y - step
                if self.board.in_bounds(x, y):
                    result.append((x, y))

        elif cannon.mouth == "D":
            for step in range(1, distance + 1):
                x = mouth_x
                y = mouth_y + step
                if self.board.in_bounds(x, y):
                    result.append((x, y))

        return result

    def _signed_value(self, piece: Piece | None, firing_color: str) -> int:
        if piece is None:
            return 0

        if piece.color == firing_color:
            return piece.level

        return -piece.level

    def _piece_from_signed_value(self, value: int, firing_color: str) -> Piece | None:
        if value == 0:
            return None

        level = min(5, abs(value))

        if value > 0:
            return Piece(firing_color, level)

        return Piece(self.opponent(firing_color), level)

    def get_local_region(self, x: int, y: int) -> List[Position]:
        region: List[Position] = []

        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if self.board.in_bounds(nx, ny):
                    region.append((nx, ny))

        return region

    def _piece_text(self, piece: Piece | None) -> str:
        if piece is None:
            return "空"
        return piece.short()

    def fire_report_text(self) -> str:
        if not self.last_fire_report_lines:
            return "本次没有发炮明细。"

        return "\n".join(self.last_fire_report_lines)

    def fire_cannon_by_index(self, index: int) -> None:
        if self.phase != "fire":
            raise ValueError("当前不是打炮阶段，不能发炮。")

        if not (1 <= index <= len(self.fire_cannon_pool)):
            raise ValueError("可发射炮编号无效。")

        cannon = self.fire_cannon_pool.pop(index - 1)
        firing_color = self.current_player
        self.chain_pass_count = 0

        before_cannons = self.get_cannons_by_color(self.current_player)
        self.clear_last_change_reached()
        self.last_fire_report_lines = []

        self.last_fire_report_lines.append("本次发炮明细：")
        self.last_fire_report_lines.append(
            f"  发射炮管：{self.player_name(firing_color)} {cannon.short()}"
        )

        # 1. 前方攻击：基于发射前棋盘记录变化
        front_positions = self._front_positions(cannon)
        front_report_lines: List[str] = []

        if front_positions:
            self.last_fire_report_lines.append("  前方作用格：")
        else:
            self.last_fire_report_lines.append("  前方作用格：无")

        front_updates_map: dict[Position, Piece | None] = {}

        for pos in front_positions:
            x, y = pos
            old_piece = self.board.get(x, y)
            old_value = self._signed_value(old_piece, firing_color)
            new_value = old_value + cannon.level
            new_piece = self._piece_from_signed_value(new_value, firing_color)

            front_updates_map[pos] = new_piece

            front_report_lines.append(
                f"    ({x}, {y}): {self._piece_text(old_piece)} -> {self._piece_text(new_piece)}"
            )

        self.last_fire_report_lines.extend(front_report_lines)

        # 2. 炮体内部升级：距炮口奇数距离的棋子 +1
        positions_from_mouth = self._cannon_positions_from_mouth(cannon)
        body_upgrade_lines: List[str] = []

        for distance, (x, y) in enumerate(positions_from_mouth):
            if distance % 2 == 1:
                piece = self.board.get(x, y)
                if piece is not None:
                    old_text = piece.short()
                    piece.level = min(5, piece.level + 1)
                    new_text = piece.short()

                    # 记录“本次变化中达到的新等级”
                    self.mark_reached_level(x, y, piece.color, piece.level)

                    if old_text != new_text:
                        body_upgrade_lines.append(
                            f"    ({x}, {y}): {old_text} -> {new_text}"
                        )

        if body_upgrade_lines:
            self.last_fire_report_lines.append("  炮体内部升级：")
            self.last_fire_report_lines.extend(body_upgrade_lines)
        else:
            self.last_fire_report_lines.append("  炮体内部升级：无")

        # 3. 统一写回前方攻击结果，并记录本次变化达到的等级
        for (x, y), new_piece in front_updates_map.items():
            self.board.set(x, y, new_piece)

            if new_piece is not None:
                self.mark_reached_level(x, y, new_piece.color, new_piece.level)

        self.history.append(
            f"{self.player_name(firing_color)}: 发射 {cannon.short()}"
        )

        after_cannons = self.get_cannons_by_color(self.current_player)

        self.last_new_cannons = self.detect_new_cannons(before_cannons, after_cannons)
        self.assign_muzzles_for_new_cannons()

        if self.last_new_cannons:
            self.last_fire_report_lines.append("  新形成炮管：")
            for new_cannon in self.last_new_cannons:
                self.last_fire_report_lines.append(
                    f"    {self.player_name(new_cannon.color)} {new_cannon.short()}"
                )
        else:
            self.last_fire_report_lines.append("  新形成炮管：无")

        self.waiting_new_pool_cannons = self.last_new_cannons.copy()

        if self.pending_muzzle_cannons:
            self.phase = "muzzle"
        else:
            self.add_waiting_new_cannons_to_pool()
            self.phase = "eat"

        self.advance_turn()

    def end_turn(self) -> None:
        self.current_player = self.opponent(self.current_player)
        self.turn_number += 1

        self.phase = "drop"
        self.pending_muzzle_cannons = []
        self.last_new_cannons = []
        self.fire_cannon_pool = []
        self.waiting_new_pool_cannons = []
        self.last_change_reached = {}
        self.last_fire_report_lines = []

    def status_text(self) -> str:
        color = self.current_player
        place_count = len(self.legal_place_positions(color))
        upgrade_count = len(self.legal_upgrade_positions(color))
        total_count = place_count + upgrade_count

        return (
            f"第 {self.turn_number} 回合 | 当前行动方：{self.player_name(color)} | 当前阶段：{self.phase_name()}\n"
            f"可操作总数：{total_count} | 其中可放置：{place_count} | 可升级：{upgrade_count}"
        )

    def is_capturable(self, x: int, y: int, attacker_color: str) -> bool:
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

        # “己方棋子数不少于被吃棋子周围格子数的一半”
        if friendly_count * 2 < len(region) - 1:
            return False

        # “己方总等级严格大于对方”
        if friendly_total <= enemy_total:
            return False

        return True

    def get_capturable_targets(self, attacker_color: str) -> List[Position]:
        result: List[Position] = []

        for y in range(1, self.board.SIZE + 1):
            for x in range(1, self.board.SIZE + 1):
                if self.is_capturable(x, y, attacker_color):
                    result.append((x, y))

        return result

    def capturable_report(self) -> str:
        targets = self.get_capturable_targets(self.current_player)

        lines: List[str] = []
        lines.append(f"{self.player_name(self.current_player)} 当前可吃目标：")

        if not targets:
            lines.append("  （暂无）")
        else:
            for i, (x, y) in enumerate(targets, start=1):
                piece = self.board.get(x, y)
                if piece is not None:
                    lines.append(f"  {i}. ({x}, {y}) {piece.short()}")

        return "\n".join(lines)

    def eat_target_by_index(self, index: int) -> None:
        if self.phase != "eat":
            raise ValueError("当前不是吃子阶段，不能执行吃子。")

        targets = self.get_capturable_targets(self.current_player)

        if not (1 <= index <= len(targets)):
            raise ValueError("可吃目标编号无效。")

        x, y = targets[index - 1]
        old_piece = self.board.get(x, y)

        if old_piece is None:
            raise ValueError("目标位置为空，无法吃子。")

        self.chain_pass_count = 0
        before_cannons = self.get_cannons_by_color(self.current_player)
        self.clear_last_change_reached()

        self.board.set(x, y, Piece(self.current_player, 1))
        self.mark_reached_level(x, y, self.current_player, 1)

        self.history.append(
            f"{self.player_name(self.current_player)}: 吃掉 ({x}, {y}) 的 {old_piece.short()}，并在原地放置1级棋子"
        )

        after_cannons = self.get_cannons_by_color(self.current_player)

        self.last_new_cannons = self.detect_new_cannons(before_cannons, after_cannons)
        self.assign_muzzles_for_new_cannons()

        self.waiting_new_pool_cannons = self.last_new_cannons.copy()

        if self.pending_muzzle_cannons:
            self.phase = "muzzle"
        else:
            self.add_waiting_new_cannons_to_pool()
            self.phase = "fire"

        self.advance_turn()

    # 进阶函数：直接结束当前回合，进入下一回合的落子阶段。通常在当前回合的打炮/吃子阶段无法继续时调用。
    def finish_full_round(self) -> None:
        next_drop_player = (
            self.opponent(self.round_drop_player)
            if self.round_drop_player is not None
            else self.opponent(self.current_player)
        )

        self.current_player = next_drop_player
        self.turn_number += 1

        self.phase = "drop"
        self.round_drop_player = None
        self.chain_pass_count = 0

        self.pending_muzzle_cannons = []
        self.last_new_cannons = []
        self.fire_cannon_pool = []
        self.waiting_new_pool_cannons = []
        self.last_change_reached = {}
        self.last_fire_report_lines = []

    # 进阶函数：在打炮或吃子阶段结束后调用，自动检查当前方是否还有可继续的操作（打炮或吃子）
    # 如果没有则自动切换到另一方的结算阶段；如果连续两方都无法继续，则结束整个大回合，进入下一回合的落子阶段。
    def advance_turn(self) -> None:
        while True:
            # 1. 炮口选择阶段：必须停下来等玩家选择
            if self.phase == "muzzle":
                return

            # 2. 打炮阶段：若还有炮可发，停下来等玩家选择
            if self.phase == "fire":
                if self.get_fireable_cannons():
                    return
                self.phase = "eat"
                continue

            # 3. 吃子阶段：若还有可吃目标，停下来等玩家选择
            if self.phase == "eat":
                if self.get_capturable_targets(self.current_player):
                    return

                # 当前方已经无法继续结算
                self.chain_pass_count += 1

                # 若连续两方都无法继续，则整个大回合结束
                if self.chain_pass_count >= 2:
                    self.finish_full_round()
                    return

                # 否则切换到另一方，开始它的结算阶段
                self.current_player = self.opponent(self.current_player)
                self.start_resolution_for_current_player()
                continue

            # 4. 落子阶段或其他阶段，不自动推进
            return
        
    # 计算指定颜色棋子的总等级和评分，用于评估局面等功能
    def piece_sum(self, color: str) -> int:
        total = 0

        for y in range(1, self.board.SIZE + 1):
            for x in range(1, self.board.SIZE + 1):
                piece = self.board.get(x, y)
                if piece is not None and piece.color == color:
                    total += piece.level

        return total

    def calculate_score(self) -> tuple[int, int]:
        red_score = self.piece_sum("R")
        blue_score = self.piece_sum("B") + 9
        return red_score, blue_score

    # 根据双方得分判断胜负，返回 "R"、"B" 或 None（平局）
    def determine_winner_by_score(self) -> str | None:
        red_score, blue_score = self.calculate_score()

        if red_score > blue_score:
            return "R"
        if blue_score > red_score:
            return "B"
        return None

    # 生成游戏结束报告，包含双方得分、胜负结果等信息
    def game_result_report(self) -> str:
        red_score, blue_score = self.calculate_score()
        winner = self.determine_winner_by_score()

        lines: List[str] = []
        lines.append("游戏结束")
        lines.append(f"结束原因：{self.player_name(self.current_player)}在落子阶段无合法操作")
        lines.append(f"红方总分：{red_score}")
        lines.append(f"蓝方总分：{blue_score}（已含补偿）")

        if winner is None:
            lines.append("结果：平局")
        else:
            lines.append(f"胜者：{self.player_name(winner)}")

        return "\n".join(lines)