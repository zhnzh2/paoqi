#game.py
from __future__ import annotations

from typing import Any, List

from core.board import Board, Position
from core.models import Piece, Cannon
from core.cannon import (
    find_all_cannons,
    cannon_signature,
    cannon_contains,
    detect_new_cannons,
    auto_determine_mouth,
    front_positions,
)

from core.undo import snapshot_state, restore_state, copy_cannon
from core.resolution import (
    collect_front_updates,
    collect_body_updates,
    apply_piece_updates,
    merge_reached_from_updates,
)
from core.record import (
    player_name,
    format_pos,
    format_cannon_for_record,
    format_cannon_with_mouth_for_record,
    piece_text,
)
from core.state_io import (
    deserialize_cannon_data,
    deserialize_piece_data,
    export_board_state,
    export_cannon_list,
    export_full_state,
    export_import_roundtrip_snapshot,
    from_exported_state,
    get_all_cannons_snapshot,
    get_board_snapshot,
    get_cannon_snapshot,
    get_drop_legal_snapshot,
    get_interaction_snapshot,
    get_log_snapshot,
    get_phase_snapshot,
    get_state_snapshot,
    import_full_state,
    phase_code,
    serialize_cannon,
    serialize_piece_at,
    serialize_position,
    winner_code,
)
from core.events import (
    add_last_action_event,
    clear_last_action_events,
    get_last_action_events,
    make_event,
    make_piece_change_event,
    make_position_event_payload,
    record_phase_change_event,
    record_turn_change_event,
)
from core.game_legal import (
    action_label_impl,
    action_with_label_impl,
    action_to_command_text_impl,
    legal_action_command_texts_impl,
    get_legal_drop_actions_impl,
    get_legal_muzzle_actions_impl,
    get_legal_fire_actions_impl,
    get_legal_eat_actions_impl,
    get_legal_actions_impl,
    get_legal_actions_snapshot_impl,
    get_action_api_snapshot_impl,
    has_single_legal_action_impl,
    get_single_legal_action_impl,
    is_action_legal_impl,
    actions_equal_for_execution_impl,
)
from core.game_flow import (
    start_resolution_for_current_player_impl,
    has_pending_muzzle_choice_impl,
    all_legal_moves_impl,
    can_player_move_impl,
    check_game_over_at_turn_start_impl,
    end_turn_impl,
    finish_full_round_impl,
    advance_turn_impl,
    calculate_score_impl,
    determine_winner_by_score_impl,
    finish_game_impl,
    finish_by_agreement_impl,
    resign_impl,
)
from core.game_actions import (
    apply_move_action_impl,
    apply_move_at_impl,
    apply_muzzle_choice_impl,
    apply_fire_choice_impl,
    apply_eat_choice_impl,
    apply_muzzle_action_impl,
    apply_fire_action_impl,
    apply_eat_action_impl,
    dispatch_action_impl,
    apply_action_impl,
    try_apply_action_impl,
    apply_action_with_snapshot_impl,
    try_apply_action_with_snapshot_impl,
    apply_single_legal_action_impl,
)
from core.game_cannon import (
    remove_contained_old_cannons_impl,
    get_all_cannons_impl,
    apply_saved_mouth_to_cannon_impl,
    initialize_fire_cannon_pool_impl,
    get_cannons_by_color_impl,
    assign_muzzles_for_new_cannons_impl,
    add_waiting_new_cannons_to_pool_impl,
    set_cannon_mouth_impl,
    all_pending_muzzles_set_impl,
    clear_pending_muzzles_impl,
    get_phase_relevant_cannons_impl,
    get_fireable_cannons_impl,
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
        self.game_over_reason: str | None = None

        # 炮管记谱模式
        # 1 = 当前简洁形式（沿用 cannon.short()）
        # 2 = 规范五元组形式：(k, n, A, 方, 向)
        self.cannon_record_style = 1

        self.last_new_cannons: List[Cannon] = []
        self.pending_muzzle_cannons: List[Cannon] = []
        self.last_fire_report_lines: List[str] = []
        self.auto_action_messages: List[str] = []
        self.last_change_reached: dict[Position, tuple[str, int]] = {}

        # 最近一次主动动作产生的结构化事件
        self.last_action_events: List[dict[str, Any]] = []

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

        # 待自动执行动作（例如唯一可发射炮、唯一可吃目标）
        self.pending_auto_action: dict[str, Any] | None = None
        self.pending_auto_message: str = ""

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

    def has_pending_auto_action(self) -> bool:
        return self.pending_auto_action is not None

    def clear_pending_auto_action(self) -> None:
        self.pending_auto_action = None
        self.pending_auto_message = ""

    def set_pending_auto_action(self, action: dict[str, Any], message: str) -> None:
        self.pending_auto_action = action
        self.pending_auto_message = message

    #from state_io.py
    def phase_code(self) -> str:
        return phase_code(self)
    def winner_code(self) -> str | None:
        return winner_code(self)
    def _serialize_piece_at(self, x: int, y: int) -> dict[str, Any] | None:
        return serialize_piece_at(self, x, y)
    def _serialize_position(self, pos: Position) -> dict[str, int]:
        return serialize_position(pos)
    def _serialize_cannon(self, cannon: Cannon) -> dict[str, Any]:
        return serialize_cannon(self, cannon)
    def _deserialize_piece_data(self, data: dict[str, Any] | None) -> Piece | None:
        return deserialize_piece_data(data)
    def _deserialize_cannon_data(self, data: dict[str, Any]) -> Cannon:
        return deserialize_cannon_data(data)

    #from state_io.py
    def export_board_state(self) -> list[list[dict[str, Any] | None]]:
        return export_board_state(self)
    def export_cannon_list(self, cannons: List[Cannon]) -> list[dict[str, Any]]:
        return export_cannon_list(self, cannons)
    def export_full_state(self) -> dict[str, Any]:
        return export_full_state(self)

    #from state_io.py
    def get_board_snapshot(self) -> list[list[dict[str, Any] | None]]:
        return get_board_snapshot(self)
    def get_cannon_snapshot(self, cannons: List[Cannon]) -> list[dict[str, Any]]:
        return get_cannon_snapshot(self, cannons)
    def get_all_cannons_snapshot(self) -> dict[str, list[dict[str, Any]]]:
        return get_all_cannons_snapshot(self)
    def get_phase_snapshot(self) -> dict[str, Any]:
        return get_phase_snapshot(self)
    def get_interaction_snapshot(self) -> dict[str, Any]:
        return get_interaction_snapshot(self)
    def get_log_snapshot(self) -> dict[str, Any]:
        return get_log_snapshot(self)
    def get_drop_legal_snapshot(self) -> dict[str, Any]:
        return get_drop_legal_snapshot(self)
    def get_state_snapshot(self) -> dict[str, Any]:
        return get_state_snapshot(self)

    #from state_io.py
    def import_full_state(self, data: dict[str, Any]) -> None:
        import_full_state(self, data)
    @classmethod
    def from_exported_state(cls, data: dict[str, Any]) -> "Game":
        return from_exported_state(data)
    def export_import_roundtrip_snapshot(self) -> dict[str, Any]:
        return export_import_roundtrip_snapshot(self)

    #from events.py
    def _make_event(self, event_type: str, **payload: Any) -> dict[str, Any]:
        return make_event(event_type, **payload)
    def _make_position_event_payload(self, x: int, y: int) -> dict[str, int]:
        return make_position_event_payload(x, y)
    def _make_piece_change_event(
        self, x: int, y: int,
        before_piece: dict[str, Any] | None, after_piece: dict[str, Any] | None, reason: str,
    ) -> dict[str, Any]:
        return make_piece_change_event(x, y, before_piece, after_piece, reason)
    
    #from events.py
    def _record_phase_change_event(self) -> None:
        record_phase_change_event(self)
    def _record_turn_change_event(self, reason: str) -> None:
        record_turn_change_event(self, reason)

    #from events.py
    def clear_last_action_events(self) -> None:
        clear_last_action_events(self)
    def add_last_action_event(self, event: dict[str, Any]) -> None:
        add_last_action_event(self, event)
    def get_last_action_events(self) -> list[dict[str, Any]]:
        return get_last_action_events(self)

    #from game_legal.py
    def _action_label(self, action: dict[str, Any]) -> str:
        return action_label_impl(self, action)
    def _action_with_label(self, action: dict[str, Any]) -> dict[str, Any]:
        return action_with_label_impl(self, action)
    def action_to_command_text(self, action: dict[str, Any]) -> str:
        return action_to_command_text_impl(self, action)
    def legal_action_command_texts(self) -> list[str]:
        return legal_action_command_texts_impl(self)
    def get_legal_drop_actions(self) -> list[dict[str, Any]]:
        return get_legal_drop_actions_impl(self)
    def get_legal_muzzle_actions(self) -> list[dict[str, Any]]:
        return get_legal_muzzle_actions_impl(self)
    def get_legal_fire_actions(self) -> list[dict[str, Any]]:
        return get_legal_fire_actions_impl(self)
    def get_legal_eat_actions(self) -> list[dict[str, Any]]:
        return get_legal_eat_actions_impl(self)
    def get_legal_actions(self) -> list[dict[str, Any]]:
        return get_legal_actions_impl(self)
    def get_legal_actions_snapshot(self) -> dict[str, Any]:
        return get_legal_actions_snapshot_impl(self)
    def get_action_api_snapshot(self) -> dict[str, Any]:
        return get_action_api_snapshot_impl(self)
    def has_single_legal_action(self) -> bool:
        return has_single_legal_action_impl(self)
    def get_single_legal_action(self) -> dict[str, Any] | None:
        return get_single_legal_action_impl(self)
    def is_action_legal(self, action: dict[str, Any]) -> bool:
        return is_action_legal_impl(self, action)
    def _actions_equal_for_execution(
        self,
        action1: dict[str, Any],
        action2: dict[str, Any],
    ) -> bool:
        return actions_equal_for_execution_impl(self, action1, action2)

    #from game_actions.py
    def _apply_move_action(self, action: dict[str, Any]) -> None:
        return apply_move_action_impl(self, action)
    def _apply_muzzle_action(self, action: dict[str, Any]) -> None:
        return apply_muzzle_action_impl(self, action)
    def _apply_fire_action(self, action: dict[str, Any]) -> None:
        return apply_fire_action_impl(self, action)
    def _apply_eat_action(self, action: dict[str, Any]) -> None:
        return apply_eat_action_impl(self, action)
    def apply_move_at(self, x: int, y: int) -> None:
        return apply_move_at_impl(self, x, y)
    def apply_muzzle_choice(self, index: int, direction: str) -> None:
        return apply_muzzle_choice_impl(self, index, direction)
    def apply_fire_choice(self, index: int) -> None:
        return apply_fire_choice_impl(self, index)
    def apply_eat_choice(self, index: int) -> None:
        return apply_eat_choice_impl(self, index)
    def _dispatch_action(self, action: dict[str, Any]) -> None:
        return dispatch_action_impl(self, action)
    def apply_action(self, action: dict[str, Any]) -> None:
        return apply_action_impl(self, action)
    def try_apply_action(self, action: dict[str, Any]) -> tuple[bool, str]:
        return try_apply_action_impl(self, action)
    def apply_action_with_snapshot(
        self,
        action: dict[str, Any],
    ) -> dict[str, Any]:
        return apply_action_with_snapshot_impl(self, action)
    def try_apply_action_with_snapshot(
        self,
        action: dict[str, Any],
    ) -> dict[str, Any]:
        return try_apply_action_with_snapshot_impl(self, action)
    def apply_single_legal_action(self) -> dict[str, Any]:
        return apply_single_legal_action_impl(self)

    def history_text(self) -> str:
        from core.record import history_text
        return history_text(self.history)


    def debug_text(self) -> str:
        from core.record import debug_text
        return debug_text(self.debug_log)

    def fire_report_text(self) -> str:
        from core.record import fire_report_text
        return fire_report_text(self.last_fire_report_lines)
    
    def add_auto_action_message(self, text: str) -> None:
        self.auto_action_messages.append(text)

    def consume_auto_action_messages(self) -> List[str]:
        messages = self.auto_action_messages.copy()
        self.auto_action_messages.clear()
        return messages
    
    #from game_flow.py
    def start_resolution_for_current_player(self) -> None:
        return start_resolution_for_current_player_impl(self)
    def has_pending_muzzle_choice(self) -> bool:
        return has_pending_muzzle_choice_impl(self)
    def all_legal_moves(self, color: str) -> List[str]:
        return all_legal_moves_impl(self, color)
    def can_player_move(self, color: str) -> bool:
        return can_player_move_impl(self, color)
    def check_game_over_at_turn_start(self) -> bool:
        return check_game_over_at_turn_start_impl(self)

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

    #from game_cannon.py
    def remove_contained_old_cannons(self, new_cannon: Cannon) -> None:
        return remove_contained_old_cannons_impl(self, new_cannon)
    def get_all_cannons(self) -> List[Cannon]:
        return get_all_cannons_impl(self)
    def _apply_saved_mouth_to_cannon(self, cannon: Cannon) -> Cannon:
        return apply_saved_mouth_to_cannon_impl(self, cannon)
    def initialize_fire_cannon_pool(self) -> None:
        return initialize_fire_cannon_pool_impl(self)
    def get_cannons_by_color(self, color: str) -> List[Cannon]:
        return get_cannons_by_color_impl(self, color)
    def assign_muzzles_for_new_cannons(self) -> None:
        return assign_muzzles_for_new_cannons_impl(self)
    def add_waiting_new_cannons_to_pool(self) -> None:
        return add_waiting_new_cannons_to_pool_impl(self)
    def set_cannon_mouth(self, index: int, direction_text: str) -> None:
        return set_cannon_mouth_impl(self, index, direction_text)
    def all_pending_muzzles_set(self) -> bool:
        return all_pending_muzzles_set_impl(self)
    def clear_pending_muzzles(self) -> None:
        return clear_pending_muzzles_impl(self)
    def get_phase_relevant_cannons(self) -> List[Cannon]:
        return get_phase_relevant_cannons_impl(self)
    def get_fireable_cannons(self) -> List[Cannon]:
        return get_fireable_cannons_impl(self)

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

        self.apply_move_at(x, y)

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
        # 记录前方攻击导致的变化事件（炮体内部升级的变化事件将在后续 apply_piece_updates 时统一记录）
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

    #from game_flow.py
    def end_turn(self) -> None:
        return end_turn_impl(self)
    def finish_full_round(self) -> None:
        return finish_full_round_impl(self)
    def advance_turn(self) -> None:
        return advance_turn_impl(self)
    def calculate_score(self) -> tuple[int, int]:
        return calculate_score_impl(self)
    def calculate_score(self) -> tuple[int, int]:
        return calculate_score_impl(self)
    def finish_game(
        self,
        reason: str,
        winner: str | None = None,
    ) -> None:
        return finish_game_impl(self, reason, winner)
    def finish_by_agreement(self) -> None:
        return finish_by_agreement_impl(self)
    def resign(self, resigning_player: str | None = None) -> None:
        return resign_impl(self, resigning_player)

    def new_cannons_report(self) -> str:
        from core.record import new_cannons_report
        return new_cannons_report(self.last_new_cannons)

    def cannon_report(self) -> str:
        from core.record import cannon_report
        return cannon_report(
            self.get_cannons_by_color("R"),
            self.get_cannons_by_color("B"),
        )

    def pending_muzzle_report(self) -> str:
        from core.record import pending_muzzle_report
        return pending_muzzle_report(self.pending_muzzle_cannons)

    def fireable_report(self) -> str:
        from core.record import fireable_report
        return fireable_report(self.current_player, self.get_fireable_cannons())

    def capturable_report(self) -> str:
        from core.record import capturable_report
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

    def clone(self) -> "Game":
        return Game.from_exported_state(self.export_full_state())

    def is_terminal(self) -> bool:
        if self.game_over:
            return True

        if self.phase == "drop" and not self.can_player_move(self.current_player):
            return True

        return False

    def get_winner(self) -> str | None:
        if not self.is_terminal():
            return None

        if self.winner is not None:
            return self.winner

        return self.determine_winner_by_score()