#game.py
from __future__ import annotations

from typing import List

from board import Board, Position
from models import Piece, Cannon
from cannon import (
    find_all_cannons,
    cannon_signature,
    cannon_contains,
    detect_new_cannons,
    auto_determine_mouth,
    front_positions,
)

from undo import snapshot_state, restore_state, copy_cannon
from resolution import (
    collect_front_updates,
    collect_body_updates,
    apply_piece_updates,
    merge_reached_from_updates,
)

from record import (
    player_name,
    format_pos,
    mouth_text,
    cannon_direction_text,
    format_cannon_for_record,
    format_cannon_with_mouth_for_record,
    piece_text,
)

class Game:
    def __init__(self) -> None:
        self.board = Board()
        self.board.setup_initial()

        self.current_player = "R"   # 红先
        self.turn_number = 1

        # 正式棋谱：只记录对局中允许展示的正式事件
        self.history: List[str] = []

        # 调试日志：记录程序内部状态变化，便于开发调试
        self.debug_log: List[str] = []

        # 操作记录：按输入顺序记录所有有效执行的命令，便于存档/复盘
        self.command_log: List[str] = []

        # 撤销栈：每次玩家主动操作前保存完整状态快照
        self.undo_stack: List[dict] = []

        self.game_over = False
        self.winner: str | None = None

        # 炮管记谱模式
        # 1 = 当前简洁形式（沿用 cannon.short()）
        # 2 = 规范五元组形式：(k, n, A, 方, 向)
        self.cannon_record_style = 1

        self.last_new_cannons: List[Cannon] = []
        self.pending_muzzle_cannons: List[Cannon] = []
        self.last_fire_report_lines: List[str] = []
        self.auto_action_messages: List[str] = []
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

    def opponent(self, color: str) -> str:
        return "B" if color == "R" else "R"

    def debug(self, text: str) -> None:
        self.debug_log.append(text)

    def record(self, text: str) -> None:
        self.history.append(text)

    def log_command(self, text: str) -> None:
        self.command_log.append(text)

    def command_log_text(self) -> str:
        if not self.command_log:
            return "当前还没有操作记录。"

        lines = ["操作记录："]
        for i, item in enumerate(self.command_log, start=1):
            #lines.append(f"  {i}. {item}")
            lines.append(f"{item}")
        return "\n".join(lines)

    def set_cannon_record_style(self, style: int) -> None:
        if style not in (1, 2):
            raise ValueError("炮管记谱模式只能是 1 或 2。")

        self.cannon_record_style = style

    def cannon_record_style_text(self) -> str:
        if self.cannon_record_style == 1:
            return "当前简洁记谱"

        if self.cannon_record_style == 2:
            return "规范五元组记谱"

        return f"未知记谱模式({self.cannon_record_style})"

    def push_undo_snapshot(self) -> None:
        self.undo_stack.append(snapshot_state(self))

    def can_undo(self) -> bool:
        return bool(self.undo_stack)

    def undo(self) -> None:
        if not self.undo_stack:
            raise ValueError("当前没有可撤销的操作。")

        snapshot = self.undo_stack.pop()
        restore_state(self, snapshot)
    
    def record_new_cannons(
        self,
        cannons: List[Cannon],
        manual_signature_to_mouth: dict[tuple, str] | None = None,
    ) -> None:
        if not cannons:
            return

        texts: List[str] = []

        for cannon in cannons:
            sig = cannon_signature(cannon)

            if manual_signature_to_mouth is not None and sig in manual_signature_to_mouth:
                mouth = manual_signature_to_mouth[sig]
                copied = copy_cannon(cannon)
                copied.mouth = mouth
                texts.append(format_cannon_with_mouth_for_record(copied, self.cannon_record_style))
            else:
                texts.append(format_cannon_for_record(cannon, self.cannon_record_style))

        player = player_name(cannons[0].color)

        if len(texts) == 1:
            self.record(f"{player}形成{texts[0]}")
        else:
            joined = "、".join(texts)
            self.record(f"{player}同时形成{joined}")

    def record_fire(self, cannon: Cannon) -> None:
        self.record(
            f"{player_name(cannon.color)}打了{format_cannon_for_record(cannon, self.cannon_record_style)}"
        )

    def record_capture(self, pos: Position) -> None:
        self.record(
            f"{player_name(self.current_player)}吃了{format_pos(pos)}处棋子"
        )

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

    def history_text(self) -> str:
        from record import history_text
        return history_text(self.history)


    def debug_text(self) -> str:
        from record import debug_text
        return debug_text(self.debug_log)

    def fire_report_text(self) -> str:
        from record import fire_report_text
        return fire_report_text(self.last_fire_report_lines)
    
    def add_auto_action_message(self, text: str) -> None:
        self.auto_action_messages.append(text)

    def consume_auto_action_messages(self) -> List[str]:
        messages = self.auto_action_messages.copy()
        self.auto_action_messages.clear()
        return messages
    
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
                mouth = auto_determine_mouth(cannon, self.last_change_reached)
                if mouth is None:
                    self.pending_muzzle_cannons.append(cannon)
                    self.waiting_new_pool_cannons.append(cannon)
                else:
                    cannon.mouth = mouth
                    self.cannon_mouth_map[cannon_signature(cannon)] = mouth

            if cannon.mouth is not None:
                self.fire_cannon_pool.append(cannon)

        if self.pending_muzzle_cannons:
            self.phase = "muzzle"
        else:
            self.phase = "fire"

    def has_pending_muzzle_choice(self) -> bool:
        return bool(self.pending_muzzle_cannons)

    def all_legal_moves(self, color: str) -> List[str]:
        moves: List[str] = []

        for x, y in self.board.legal_place_positions(color):
            moves.append(f"move {x} {y}   [放置]")

        for x, y in self.board.legal_upgrade_positions(color):
            piece = self.board.get(x, y)
            if piece is not None:
                moves.append(f"move {x} {y}   [升级到{piece.level + 1}级]")

        return moves

    def can_player_move(self, color: str) -> bool:
        return bool(self.board.legal_place_positions(color) or self.board.legal_upgrade_positions(color))

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
        self.record(f"{player_name(color)}在({x}, {y})落子")

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

        self.debug(
            f"{player_name(color)}: 将 ({x}, {y}) 从{old_level}级升级到{piece.level}级"
        )
        self.record(f"{player_name(color)}在({x}, {y})落子")

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

    def remove_contained_old_cannons(self, new_cannon: Cannon) -> None:
        remaining: List[Cannon] = []

        for old_cannon in self.fire_cannon_pool:
            if cannon_contains(new_cannon, old_cannon):
                self.debug(
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
        sig = cannon_signature(cannon)

        if sig in self.cannon_mouth_map:
            cannon.mouth = self.cannon_mouth_map[sig]
            return cannon

        for pending in self.pending_muzzle_cannons:
            if cannon_signature(pending) == sig and pending.mouth is not None:
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

    def assign_muzzles_for_new_cannons(self) -> None:
        self.pending_muzzle_cannons = []
        auto_resolved_cannons: List[Cannon] = []

        for cannon in self.last_new_cannons:
            mouth = auto_determine_mouth(cannon, self.last_change_reached)

            if mouth is None:
                self.pending_muzzle_cannons.append(cannon)
            else:
                cannon.mouth = mouth
                self.cannon_mouth_map[cannon_signature(cannon)] = mouth
                auto_resolved_cannons.append(cannon)

                self.debug(
                    f"{player_name(cannon.color)}: 新炮 {cannon.positions} 自动判定炮口为 {mouth}"
                )

        # 自动判口成功的新炮，立即作为“形成某炮”记入正式棋谱
        self.record_new_cannons(auto_resolved_cannons)

    def add_waiting_new_cannons_to_pool(self) -> None:
        if not self.waiting_new_pool_cannons:
            return

        for cannon in self.waiting_new_pool_cannons:
            self._apply_saved_mouth_to_cannon(cannon)

            # 先移除被新炮完全包含的旧炮
            self.remove_contained_old_cannons(cannon)

            sig = cannon_signature(cannon)
            exists = any(cannon_signature(old) == sig for old in self.fire_cannon_pool)

            if not exists:
                self.fire_cannon_pool.append(cannon)
                self.debug(
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

        self.push_undo_snapshot()
        cannon.mouth = mouth
        self.cannon_mouth_map[cannon_signature(cannon)] = mouth

        # 关键：顺手把 last_new_cannons 里对应对象也同步一下
        for new_cannon in self.last_new_cannons:
            if cannon_signature(new_cannon) == cannon_signature(cannon):
                new_cannon.mouth = mouth

        self.debug(
            f"{player_name(cannon.color)}: 为新炮 {cannon.positions} 指定炮口方向 {direction_text}"
        )

        self.record_new_cannons(
            [cannon],
            manual_signature_to_mouth={cannon_signature(cannon): mouth},
        )
        if self.all_pending_muzzles_set():
            self.add_waiting_new_cannons_to_pool()
            self.clear_pending_muzzles()
            self.phase = "fire"
            self.advance_turn()

    def all_pending_muzzles_set(self) -> bool:
        return all(c.mouth is not None for c in self.pending_muzzle_cannons)

    def clear_pending_muzzles(self) -> None:
        self.pending_muzzle_cannons = []

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
        
        self.push_undo_snapshot()
        self.clear_last_change_reached()

        # 记录这次大回合的落子发起方
        self.round_drop_player = self.current_player
        self.chain_pass_count = 0

        before_cannons = self.get_cannons_by_color(self.current_player)
        self.apply_move(x, y)
        after_cannons = self.get_cannons_by_color(self.current_player)

        self.last_new_cannons = detect_new_cannons(before_cannons, after_cannons)
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

    def get_local_region(self, x: int, y: int) -> List[Position]:
        region: List[Position] = []

        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if self.board.in_bounds(nx, ny):
                    region.append((nx, ny))

        return region

    def fire_cannon_by_index(self, index: int) -> None:
        if self.phase != "fire":
            raise ValueError("当前不是打炮阶段，不能发炮。")

        if not (1 <= index <= len(self.fire_cannon_pool)):
            raise ValueError("可发射炮编号无效。")

        self.push_undo_snapshot()
        cannon = self.fire_cannon_pool.pop(index - 1)
        firing_color = self.current_player
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
        apply_piece_updates(self.board, front_updates_map)
        merge_reached_from_updates(self.last_change_reached, front_updates_map)

        # 4. 统一写回炮体内部升级结果，并记录本次变化达到的等级
        apply_piece_updates(self.board, body_updates_map)
        merge_reached_from_updates(self.last_change_reached, body_updates_map)

        self.record_fire(cannon)

        after_cannons = self.get_cannons_by_color(self.current_player)

        self.last_new_cannons = detect_new_cannons(before_cannons, after_cannons)
        self.assign_muzzles_for_new_cannons()

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
        else:
            self.add_waiting_new_cannons_to_pool()

            # 如果当前方仍然还有可发射炮，就继续留在打炮阶段
            if self.fire_cannon_pool:
                self.phase = "fire"
            else:
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
        place_count = len(self.board.legal_place_positions(color))
        upgrade_count = len(self.board.legal_upgrade_positions(color))
        total_count = place_count + upgrade_count

        return (
            f"第 {self.turn_number} 回合 | 当前行动方：{player_name(color)} | 当前阶段：{self.phase_name()}\n"
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

    def eat_target_by_index(self, index: int) -> None:
        if self.phase != "eat":
            raise ValueError("当前不是吃子阶段，不能执行吃子。")

        targets = self.get_capturable_targets(self.current_player)

        if not (1 <= index <= len(targets)):
            raise ValueError("可吃目标编号无效。")

        self.push_undo_snapshot()
        x, y = targets[index - 1]
        old_piece = self.board.get(x, y)

        if old_piece is None:
            raise ValueError("目标位置为空，无法吃子。")

        self.chain_pass_count = 0
        before_cannons = self.get_cannons_by_color(self.current_player)
        self.clear_last_change_reached()

        self.board.set(x, y, Piece(self.current_player, 1))
        self.mark_reached_level(x, y, self.current_player, 1)

        self.record_capture((x, y))
        self.debug(
            f"{player_name(self.current_player)}: 吃掉 ({x}, {y}) 的 {old_piece.short()}，并在原地放置1级棋子"
        )

        after_cannons = self.get_cannons_by_color(self.current_player)

        self.last_new_cannons = detect_new_cannons(before_cannons, after_cannons)
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

            # 2. 打炮阶段
            if self.phase == "fire":
                fireable = self.get_fireable_cannons()

                if len(fireable) >= 2:
                    return

                if len(fireable) == 1:
                    cannon = fireable[0]

                    if self.last_new_cannons:
                        formed_text = "、".join(
                            format_cannon_for_record(c, self.cannon_record_style)
                            for c in self.last_new_cannons
                        )
                        self.add_auto_action_message(
                            f"本步形成{formed_text}\n"
                            f"当前仅有 1 门可发射炮，已自动发射 "
                            f"{format_cannon_for_record(cannon, self.cannon_record_style)}"
                        )
                    else:
                        self.add_auto_action_message(
                            f"当前仅有 1 门可发射炮，已自动发射 "
                            f"{format_cannon_for_record(cannon, self.cannon_record_style)}"
                        )

                    self.fire_cannon_by_index(1)
                    return

                self.phase = "eat"
                continue

            # 3. 吃子阶段
            if self.phase == "eat":
                targets = self.get_capturable_targets(self.current_player)

                if len(targets) >= 2:
                    return

                if len(targets) == 1:
                    x, y = targets[0]
                    self.add_auto_action_message(
                        f"当前仅有 1 个可吃目标，已自动吃掉 ({x}, {y})"
                    )
                    self.eat_target_by_index(1)
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

    def calculate_score(self) -> tuple[int, int]:
        red_score = self.board.piece_sum("R")
        blue_score = self.board.piece_sum("B") + 9
        return red_score, blue_score

    # 根据双方得分判断胜负，返回 "R"、"B" 或 None（平局）
    def determine_winner_by_score(self) -> str | None:
        red_score, blue_score = self.calculate_score()

        if red_score > blue_score:
            return "R"
        if blue_score > red_score:
            return "B"
        return None

    def new_cannons_report(self) -> str:
        from record import new_cannons_report
        return new_cannons_report(self.last_new_cannons)

    def cannon_report(self) -> str:
        from record import cannon_report
        return cannon_report(
            self.get_cannons_by_color("R"),
            self.get_cannons_by_color("B"),
        )

    def pending_muzzle_report(self) -> str:
        from record import pending_muzzle_report
        return pending_muzzle_report(self.pending_muzzle_cannons)

    def fireable_report(self) -> str:
        from record import fireable_report
        return fireable_report(self.current_player, self.get_fireable_cannons())

    def capturable_report(self) -> str:
        from record import capturable_report
        return capturable_report(
            self.current_player,
            self.get_capturable_targets(self.current_player),
            self.board,
        )

    # 生成游戏结束报告，包含双方得分、胜负结果等信息
    def game_result_report(self) -> str:
        red_score, blue_score = self.calculate_score()
        winner = self.determine_winner_by_score()

        lines: List[str] = []
        lines.append("游戏结束")
        lines.append(f"结束原因：{player_name(self.current_player)}在落子阶段无合法操作")
        lines.append(f"红方总分：{red_score}")
        lines.append(f"蓝方总分：{blue_score}（已含补偿）")

        if winner is None:
            lines.append("结果：平局")
        else:
            lines.append(f"胜者：{player_name(winner)}")

        return "\n".join(lines)