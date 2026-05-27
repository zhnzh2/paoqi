#game.py
from __future__ import annotations

from typing import Any, List

from core.board import Board, Position
from core.models import Cannon
from core.cannon import cannon_signature

from core.undo import snapshot_state, restore_state, copy_cannon
from core.record import (
    player_name,
    format_pos,
    format_cannon_for_record,
    format_cannon_with_mouth_for_record,
)
from core.state_io import (
    export_board_state,
    export_cannon_list,
    export_full_state,
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
    serialize_cannon,
    serialize_piece_at,
)
from core.events import (
    add_last_action_event,
    clear_last_action_events,
    get_last_action_events,
    make_event,
    make_piece_change_event,
    record_phase_change_event,
    record_turn_change_event,
)
from core.game_impl.legal import (
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
from core.game_impl.flow import (
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
from core.game_impl.actions import (
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
from core.game_impl.cannon_mgmt import (
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
from core.game_impl.fire import fire_cannon_by_index_impl
from core.game_impl.eat import (
    is_capturable_impl,
    get_capturable_targets_impl,
    eat_target_by_index_impl,
)
from core.game_impl.clone import clone_impl
from core.game_impl.move import apply_place_impl, apply_upgrade_impl, apply_move_impl
from core.game_impl.report import (
    cannon_report_impl,
    capturable_report_impl,
    debug_text_impl,
    fire_report_text_impl,
    fireable_report_impl,
    game_result_report_impl,
    history_text_impl,
    new_cannons_report_impl,
    pending_muzzle_report_impl,
    status_text_impl,
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

    _serialize_piece_at = serialize_piece_at
    _serialize_cannon = serialize_cannon

    export_board_state = export_board_state
    export_cannon_list = export_cannon_list
    export_full_state = export_full_state
    get_board_snapshot = get_board_snapshot
    get_cannon_snapshot = get_cannon_snapshot
    get_all_cannons_snapshot = get_all_cannons_snapshot
    get_phase_snapshot = get_phase_snapshot
    get_interaction_snapshot = get_interaction_snapshot
    get_log_snapshot = get_log_snapshot
    get_drop_legal_snapshot = get_drop_legal_snapshot
    get_state_snapshot = get_state_snapshot
    import_full_state = import_full_state
    from_exported_state = staticmethod(from_exported_state)

    _make_event = staticmethod(make_event)
    _make_piece_change_event = staticmethod(make_piece_change_event)
    _record_phase_change_event = record_phase_change_event
    _record_turn_change_event = record_turn_change_event
    clear_last_action_events = clear_last_action_events
    add_last_action_event = add_last_action_event
    get_last_action_events = get_last_action_events

    _action_label = action_label_impl
    _action_with_label = action_with_label_impl
    action_to_command_text = action_to_command_text_impl
    legal_action_command_texts = legal_action_command_texts_impl
    get_legal_drop_actions = get_legal_drop_actions_impl
    get_legal_muzzle_actions = get_legal_muzzle_actions_impl
    get_legal_fire_actions = get_legal_fire_actions_impl
    get_legal_eat_actions = get_legal_eat_actions_impl
    get_legal_actions = get_legal_actions_impl
    get_legal_actions_snapshot = get_legal_actions_snapshot_impl
    get_action_api_snapshot = get_action_api_snapshot_impl
    has_single_legal_action = has_single_legal_action_impl
    get_single_legal_action = get_single_legal_action_impl
    is_action_legal = is_action_legal_impl
    _actions_equal_for_execution = actions_equal_for_execution_impl

    _apply_move_action = apply_move_action_impl
    _apply_muzzle_action = apply_muzzle_action_impl
    _apply_fire_action = apply_fire_action_impl
    _apply_eat_action = apply_eat_action_impl
    apply_move_at = apply_move_at_impl
    apply_muzzle_choice = apply_muzzle_choice_impl
    apply_fire_choice = apply_fire_choice_impl
    apply_eat_choice = apply_eat_choice_impl
    _dispatch_action = dispatch_action_impl
    apply_action = apply_action_impl
    try_apply_action = try_apply_action_impl
    apply_action_with_snapshot = apply_action_with_snapshot_impl
    try_apply_action_with_snapshot = try_apply_action_with_snapshot_impl
    apply_single_legal_action = apply_single_legal_action_impl

    history_text = history_text_impl
    debug_text = debug_text_impl
    fire_report_text = fire_report_text_impl

    def consume_auto_action_messages(self) -> List[str]:
        messages = self.auto_action_messages.copy()
        self.auto_action_messages.clear()
        return messages
    
    start_resolution_for_current_player = start_resolution_for_current_player_impl
    has_pending_muzzle_choice = has_pending_muzzle_choice_impl
    all_legal_moves = all_legal_moves_impl
    can_player_move = can_player_move_impl
    check_game_over_at_turn_start = check_game_over_at_turn_start_impl

    apply_place = apply_place_impl
    apply_upgrade = apply_upgrade_impl
    apply_move = apply_move_impl

    remove_contained_old_cannons = remove_contained_old_cannons_impl
    get_all_cannons = get_all_cannons_impl
    _apply_saved_mouth_to_cannon = apply_saved_mouth_to_cannon_impl
    initialize_fire_cannon_pool = initialize_fire_cannon_pool_impl
    get_cannons_by_color = get_cannons_by_color_impl
    assign_muzzles_for_new_cannons = assign_muzzles_for_new_cannons_impl
    add_waiting_new_cannons_to_pool = add_waiting_new_cannons_to_pool_impl
    set_cannon_mouth = set_cannon_mouth_impl
    all_pending_muzzles_set = all_pending_muzzles_set_impl
    clear_pending_muzzles = clear_pending_muzzles_impl
    get_phase_relevant_cannons = get_phase_relevant_cannons_impl
    get_fireable_cannons = get_fireable_cannons_impl

    def get_local_region(self, x: int, y: int) -> List[Position]:
        region: List[Position] = []

        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if self.board.in_bounds(nx, ny):
                    region.append((nx, ny))

        return region

    fire_cannon_by_index = fire_cannon_by_index_impl
    status_text = status_text_impl
    is_capturable = is_capturable_impl
    get_capturable_targets = get_capturable_targets_impl
    eat_target_by_index = eat_target_by_index_impl

    end_turn = end_turn_impl
    finish_full_round = finish_full_round_impl
    advance_turn = advance_turn_impl
    calculate_score = calculate_score_impl
    determine_winner_by_score = determine_winner_by_score_impl
    finish_game = finish_game_impl
    finish_by_agreement = finish_by_agreement_impl
    resign = resign_impl

    new_cannons_report = new_cannons_report_impl
    cannon_report = cannon_report_impl
    pending_muzzle_report = pending_muzzle_report_impl
    fireable_report = fireable_report_impl
    capturable_report = capturable_report_impl
    game_result_report = game_result_report_impl
    clone = clone_impl

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
