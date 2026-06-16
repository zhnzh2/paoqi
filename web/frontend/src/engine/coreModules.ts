// 自动生成的文件，请勿手动编辑。
// 由 scripts/bundleCoreModules.js 生成。
// 包含 core/ 目录下所有 .py 模块的内容。

const CORE_MODULES: Record<string, string> = {
  "AI.py": `# AI.py
from __future__ import annotations

import random

from math import inf
from typing import Any

from core.game import Game

def evaluate(game: Game, perspective: str) -> float:
    if game.is_terminal():
        winner = game.get_winner()
        if winner == perspective:
            return 100000.0
        if winner is None:
            return 0.0
        return -100000.0

    opponent = game.opponent(perspective)

    my_piece_count = game.board.count_pieces(perspective)
    opp_piece_count = game.board.count_pieces(opponent)

    my_total_level = game.board.piece_sum(perspective)
    opp_total_level = game.board.piece_sum(opponent)

    my_cannon_count = len(game.get_cannons_by_color(perspective))
    opp_cannon_count = len(game.get_cannons_by_color(opponent))

    my_capture_count = len(game.get_capturable_targets(perspective))
    opp_capture_count = len(game.get_capturable_targets(opponent))

    my_high_level_count = count_high_level_pieces(game, perspective)
    opp_high_level_count = count_high_level_pieces(game, opponent)

    my_center_score = center_control_score(game, perspective)
    opp_center_score = center_control_score(game, opponent)

    score = 0.0
    score += 10.0 * (my_piece_count - opp_piece_count)
    score += 2.0 * (my_total_level - opp_total_level)
    score += 8.0 * (my_cannon_count - opp_cannon_count)
    score += 5.0 * (my_capture_count - opp_capture_count)
    score += 4.0 * (my_high_level_count - opp_high_level_count)
    score += 1.5 * (my_center_score - opp_center_score)

    return score

def action_priority(action: dict) -> int:
    action_type = action.get("type")

    if action_type == "eat":
        return 5
    if action_type == "fire":
        return 4
    if action_type == "muzzle":
        return 3
    if action_type == "move":
        mode = action.get("mode")
        if mode == "upgrade":
            return 2
        return 1

    return 0

def count_high_level_pieces(game: Game, color: str) -> int:
    count = 0
    for x in range(1, 10):
        for y in range(1, 10):
            piece = game.board.get(x, y)
            if piece is not None and piece.color == color and piece.level >= 3:
                count += 1
    return count

def center_control_score(game: Game, color: str) -> int:
    score = 0
    center_cells = [
        (4, 4), (4, 5), (4, 6),
        (5, 4), (5, 5), (5, 6),
        (6, 4), (6, 5), (6, 6),
    ]

    for x, y in center_cells:
        piece = game.board.get(x, y)
        if piece is not None and piece.color == color:
            score += piece.level

    return score

def alphabeta(
    game: Game,
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
    perspective: str,
):
    if depth == 0 or game.is_terminal():
        return evaluate(game, perspective), None

    actions = game.get_legal_actions()
    if not actions:
        return evaluate(game, perspective), None

    actions = sorted(actions, key=action_priority, reverse=True)

    best_action = None

    if maximizing:
        value = -inf
        for action in actions:
            child = game.clone()
            child.apply_action(action)

            next_maximizing = (child.current_player == perspective)

            score, _ = alphabeta(
                child,
                depth - 1,
                alpha,
                beta,
                next_maximizing,
                perspective,
            )

            if score > value:
                value = score
                best_action = action

            alpha = max(alpha, value)
            if beta <= alpha:
                break

        return value, best_action

    else:
        value = inf
        for action in actions:
            child = game.clone()
            child.apply_action(action)

            next_maximizing = (child.current_player == perspective)

            score, _ = alphabeta(
                child,
                depth - 1,
                alpha,
                beta,
                next_maximizing,
                perspective,
            )

            if score < value:
                value = score
                best_action = action

            beta = min(beta, value)
            if beta <= alpha:
                break

        return value, best_action

class AlphaBetaAgent:
    def __init__(self, color: str, depth: int = 2, verbose: bool = False, random_tiebreak: bool = True,):
        self.color = color
        self.depth = depth
        self.verbose = verbose
        self.random_tiebreak = random_tiebreak

    def choose_action(self, game: Game) -> dict[str, Any] | None:
        actions = game.get_legal_actions()
        if not actions:
            return None

        actions = sorted(actions, key=action_priority, reverse=True)

        maximizing = (game.current_player == self.color)

        best_actions = []
        if maximizing:
            best_score = -inf
        else:
            best_score = inf

        if self.verbose:
            print(
                f"\\n[AI] 玩家 {self.color} 开始搜索，"
                f"当前执子：{game.current_player}，depth={self.depth}"
            )

        for action in actions:
            child = game.clone()
            child.apply_action(action)

            next_maximizing = (child.current_player == self.color)

            score, _ = alphabeta(
                game=child,
                depth=self.depth - 1,
                alpha=-inf,
                beta=inf,
                maximizing=next_maximizing,
                perspective=self.color,
            )

            if self.verbose:
                label = action.get("label", str(action))
                print(f"[AI] 候选动作：{label} -> score = {score}")

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_actions = [action]
                elif score == best_score:
                    best_actions.append(action)
            else:
                if score < best_score:
                    best_score = score
                    best_actions = [action]
                elif score == best_score:
                    best_actions.append(action)

        best_action = None
        if best_actions:
            if self.random_tiebreak:
                best_action = random.choice(best_actions)
            else:
                best_action = best_actions[0]

        if self.verbose:
            if best_action is not None:
                label = best_action.get("label", str(best_action))
                print(f"[AI] 最终选择：{label} -> score = {best_score}")
                print(f"[AI] 同分最优动作数：{len(best_actions)}")
            else:
                print("[AI] 没有选出动作")

        return best_action
    
class GreedyAgent:
    def __init__(
        self,
        color: str,
        verbose: bool = False,
        random_tiebreak: bool = True,
    ):
        self.color = color
        self.verbose = verbose
        self.random_tiebreak = random_tiebreak

    def choose_action(self, game: Game) -> dict[str, Any] | None:
        actions = game.get_legal_actions()
        if not actions:
            return None

        actions = sorted(actions, key=action_priority, reverse=True)

        best_actions = []
        best_score = -inf

        if self.verbose:
            print(f"\\n[Greedy] 玩家 {self.color} 开始选步")

        for action in actions:
            child = game.clone()
            child.apply_action(action)

            score = evaluate(child, self.color)

            if self.verbose:
                label = action.get("label", str(action))
                print(f"[Greedy] 候选动作：{label} -> score = {score}")

            if score > best_score:
                best_score = score
                best_actions = [action]
            elif score == best_score:
                best_actions.append(action)

        best_action = None
        if best_actions:
            if self.random_tiebreak:
                best_action = random.choice(best_actions)
            else:
                best_action = best_actions[0]

        if self.verbose:
            if best_action is not None:
                label = best_action.get("label", str(best_action))
                print(f"[Greedy] 最终选择：{label} -> score = {best_score}")
                print(f"[Greedy] 同分最优动作数：{len(best_actions)}")
            else:
                print("[Greedy] 没有选出动作")

        return best_action

class RandomAgent:
    def __init__(self, color: str):
        self.color = color

    def choose_action(self, game: Game) -> dict[str, Any] | None:
        actions = game.get_legal_actions()
        if not actions:
            return None
        return random.choice(actions)`,
  "__init__.py": ``,
  "board.py": `#board.py
from __future__ import annotations

from typing import List, Optional, Tuple

from core.models import Piece

Position = Tuple[int, int]  # (x, y), both 1-based

class Board:
    SIZE = 9

    def __init__(self) -> None:
        self.grid: List[List[Optional[Piece]]] = [
            [None for _ in range(self.SIZE)] for _ in range(self.SIZE)
        ]

    def in_bounds(self, x: int, y: int) -> bool:
        return 1 <= x <= self.SIZE and 1 <= y <= self.SIZE

    def to_index(self, x: int, y: int) -> Tuple[int, int]:
        return y - 1, x - 1

    def get(self, x: int, y: int) -> Optional[Piece]:
        if not self.in_bounds(x, y):
            return None
        row, col = self.to_index(x, y)
        return self.grid[row][col]

    def set(self, x: int, y: int, piece: Optional[Piece]) -> None:
        if not self.in_bounds(x, y):
            raise ValueError(f"坐标超出棋盘范围: ({x}, {y})")
        row, col = self.to_index(x, y)
        self.grid[row][col] = piece

    def is_empty(self, x: int, y: int) -> bool:
        return self.get(x, y) is None

    def neighbors4(self, x: int, y: int) -> List[Position]:
        candidates = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [(nx, ny) for nx, ny in candidates if self.in_bounds(nx, ny)]

    def has_adjacent_friendly(self, x: int, y: int, color: str) -> bool:
        for nx, ny in self.neighbors4(x, y):
            piece = self.get(nx, ny)
            if piece is not None and piece.color == color:
                return True
        return False

    def positions_of_color(self, color: str) -> List[Position]:
        result: List[Position] = []
        for y in range(1, self.SIZE + 1):
            for x in range(1, self.SIZE + 1):
                piece = self.get(x, y)
                if piece is not None and piece.color == color:
                    result.append((x, y))
        return result

    def count_pieces(self, color: str) -> int:
        return len(self.positions_of_color(color))

    def setup_initial(self) -> None:
        # 蓝方在 (1,1)，红方在 (9,9)
        self.set(1, 1, Piece("B", 1))
        self.set(9, 9, Piece("R", 1))

    def render(self) -> str:
        lines: List[str] = []
        header = "     " + " ".join(f"{x:>2}" for x in range(1, self.SIZE + 1))
        lines.append(header)
        lines.append("    " + "-" * (self.SIZE * 3))

        for y in range(1, self.SIZE + 1):
            row_cells: List[str] = []
            for x in range(1, self.SIZE + 1):
                piece = self.get(x, y)
                cell = piece.short() if piece is not None else "."
                row_cells.append(f"{cell:>3}")
            lines.append(f"{y:>2} |" + "".join(row_cells))
        return "\\n".join(lines)
    
    def legal_place_positions(self, color: str) -> List[Position]:
        result: List[Position] = []

        for y in range(1, self.SIZE + 1):
            for x in range(1, self.SIZE + 1):
                if self.is_empty(x, y) and self.has_adjacent_friendly(x, y, color):
                    result.append((x, y))

        return result
    
    def legal_upgrade_positions(self, color: str) -> List[Position]:
        result: List[Position] = []

        for y in range(1, self.SIZE + 1):
            for x in range(1, self.SIZE + 1):
                piece = self.get(x, y)
                if piece is not None and piece.color == color and piece.level in (1, 2):
                    result.append((x, y))

        return result

    def piece_sum(self, color: str) -> int:
        total = 0

        for y in range(1, self.SIZE + 1):
            for x in range(1, self.SIZE + 1):
                piece = self.get(x, y)
                if piece is not None and piece.color == color:
                    total += piece.level

        return total`,
  "cannon.py": `#cannon
from __future__ import annotations

from typing import List, Tuple

from core.board import Board, Position
from core.models import Cannon, Piece

Position = Tuple[int, int]

def _scan_line_for_cannons(cells: List[Tuple[Position, Piece | None]], direction: str) -> List[Cannon]:
    """
    给定一整行或一整列，扫描其中所有合法炮管。
    cells 的格式： [((x, y), piece_or_none), ...]
    """
    result: List[Cannon] = []
    i = 0
    n = len(cells)

    while i < n:
        pos, piece = cells[i]

        # 空格 或 5级子 不可能作为炮管起点
        if piece is None or piece.level == 5:
            i += 1
            continue

        color = piece.color
        level = piece.level

        j = i
        positions: List[Position] = []

        while j < n:
            pos_j, piece_j = cells[j]
            if piece_j is not None and piece_j.color == color and piece_j.level == level:
                positions.append(pos_j)
                j += 1
            else:
                break

        # 这里只认最大连续段
        if len(positions) >= 3:
            result.append(
                Cannon(
                    color=color,
                    level=level,
                    positions=tuple(positions),
                    direction=direction,
                )
            )

        i = j

    return result

def find_all_cannons(board: Board) -> List[Cannon]:
    """
    扫描整个棋盘，返回当前所有炮管。
    """
    result: List[Cannon] = []

    # 扫描每一行（横向炮）
    for y in range(1, board.SIZE + 1):
        cells: List[Tuple[Position, Piece | None]] = []
        for x in range(1, board.SIZE + 1):
            cells.append(((x, y), board.get(x, y)))
        result.extend(_scan_line_for_cannons(cells, "H"))

    # 扫描每一列（纵向炮）
    for x in range(1, board.SIZE + 1):
        cells: List[Tuple[Position, Piece | None]] = []
        for y in range(1, board.SIZE + 1):
            cells.append(((x, y), board.get(x, y)))
        result.extend(_scan_line_for_cannons(cells, "V"))

    return result

def find_cannons_by_color(board: Board, color: str) -> List[Cannon]:
    return [c for c in find_all_cannons(board) if c.color == color]

def cannon_signature(cannon: Cannon) -> tuple:
    return (
        cannon.color,
        cannon.level,
        cannon.positions,
        cannon.direction,
    )

def cannon_contains(outer: Cannon, inner: Cannon) -> bool:
    if outer.color != inner.color:
        return False

    if outer.level != inner.level:
        return False

    if outer.direction != inner.direction:
        return False

    outer_set = set(outer.positions)
    inner_set = set(inner.positions)

    return inner_set.issubset(outer_set)

def detect_new_cannons(
    before_cannons: List[Cannon],
    after_cannons: List[Cannon],
) -> List[Cannon]:
    before_set = {cannon_signature(c) for c in before_cannons}
    new_cannons: List[Cannon] = []

    for cannon in after_cannons:
        if cannon_signature(cannon) not in before_set:
            new_cannons.append(cannon)

    return new_cannons

def auto_determine_mouth(
    cannon: Cannon,
    last_change_reached: dict[Position, tuple[str, int]],
) -> str | None:
    candidates: List[Position] = []

    for pos, (color, level) in last_change_reached.items():
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

def cannon_positions_from_mouth(cannon: Cannon) -> List[Position]:
    positions = list(cannon.positions)

    if cannon.mouth in ("R", "D"):
        positions.reverse()

    return positions

def front_positions(board: Board, cannon: Cannon) -> List[Position]:
    n = cannon.length
    distance = n - 2
    positions_from_mouth = cannon_positions_from_mouth(cannon)

    result: List[Position] = []

    if not positions_from_mouth:
        return result

    mouth_x, mouth_y = positions_from_mouth[0]

    if distance <= 0:
        return result

    if cannon.mouth == "L":
        for step in range(1, distance + 1):
            x = mouth_x - step
            y = mouth_y
            if board.in_bounds(x, y):
                result.append((x, y))

    elif cannon.mouth == "R":
        for step in range(1, distance + 1):
            x = mouth_x + step
            y = mouth_y
            if board.in_bounds(x, y):
                result.append((x, y))

    elif cannon.mouth == "U":
        for step in range(1, distance + 1):
            x = mouth_x
            y = mouth_y - step
            if board.in_bounds(x, y):
                result.append((x, y))

    elif cannon.mouth == "D":
        for step in range(1, distance + 1):
            x = mouth_x
            y = mouth_y + step
            if board.in_bounds(x, y):
                result.append((x, y))

    return result`,
  "events.py": `#events.py
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from core.record import player_name

if TYPE_CHECKING:
    from core.game import Game

def make_event(event_type: str, **payload: Any) -> dict[str, Any]:
    event = {"type": event_type}
    event.update(payload)
    return event

def make_piece_change_event(
    x: int,
    y: int,
    before_piece: dict[str, Any] | None,
    after_piece: dict[str, Any] | None,
    reason: str,
) -> dict[str, Any]:
    return make_event(
        "piece_change",
        x=x,
        y=y,
        before=before_piece,
        after=after_piece,
        reason=reason,
    )

def clear_last_action_events(game: "Game") -> None:
    game.last_action_events = []

def add_last_action_event(game: "Game", event: dict[str, Any]) -> None:
    game.last_action_events.append(event)

def get_last_action_events(game: "Game") -> list[dict[str, Any]]:
    return [event.copy() for event in game.last_action_events]

def record_phase_change_event(game: "Game") -> None:
    add_last_action_event(
        game,
        make_event(
            "phase_change",
            phase=game.phase,
            phase_name=game.phase_name(),
            current_player=game.current_player,
            current_player_name=player_name(game.current_player),
        ),
    )

def record_turn_change_event(game: "Game", reason: str) -> None:
    add_last_action_event(
        game,
        make_event(
            "turn_change",
            reason=reason,
            current_player=game.current_player,
            current_player_name=player_name(game.current_player),
            turn_number=game.turn_number,
            phase=game.phase,
            phase_name=game.phase_name(),
        ),
    )`,
  "game.py": `#game.py
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
        return "\\n".join(lines)

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
`,
  "game_impl/__init__.py": `# core/game_impl/__init__.py
# Game 类的方法实现模块
`,
  "game_impl/actions.py": `# core/game_impl/actions.py
from __future__ import annotations

from typing import Any

def apply_move_action_impl(self, action: dict[str, Any]) -> None:
    x = action["x"]
    y = action["y"]
    self.apply_move_at(x, y)

def apply_move_at_impl(self, x: int, y: int) -> None:
    from core.cannon import detect_new_cannons

    if self.phase != "drop":
        raise ValueError("当前阶段不是落子阶段，无法执行该操作。")

    if not self.board.in_bounds(x, y):
        raise ValueError("坐标越界。")

    before_piece = self._serialize_piece_at(x, y)

    self.push_undo_snapshot()
    self.clear_last_change_reached()
    self.clear_last_action_events()

    self.round_drop_player = self.current_player
    self.chain_pass_count = 0

    before_cannons = self.get_cannons_by_color(self.current_player)
    self.apply_move(x, y)
    after_piece = self._serialize_piece_at(x, y)
    after_cannons = self.get_cannons_by_color(self.current_player)

    move_reason = "place" if before_piece is None else "upgrade"
    self.add_last_action_event(
        self._make_piece_change_event(
            x=x,
            y=y,
            before_piece=before_piece,
            after_piece=after_piece,
            reason=move_reason,
        )
    )

    self.last_new_cannons = detect_new_cannons(before_cannons, after_cannons)
    self.assign_muzzles_for_new_cannons()

    for cannon in self.last_new_cannons:
        self.add_last_action_event(
            self._make_event(
                "new_cannon",
                cannon=self._serialize_cannon(cannon),
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

def apply_muzzle_choice_impl(self, index: int, direction: str) -> None:
    self.set_cannon_mouth(index, direction)

def apply_fire_choice_impl(self, index: int) -> None:
    self.fire_cannon_by_index(index)

def apply_eat_choice_impl(self, index: int) -> None:
    self.eat_target_by_index(index)

def apply_muzzle_action_impl(self, action: dict[str, Any]) -> None:
    index = action["index"]
    direction = action["direction"]
    self.apply_muzzle_choice(index, direction)

def apply_fire_action_impl(self, action: dict[str, Any]) -> None:
    index = action["index"]
    self.apply_fire_choice(index)

def apply_eat_action_impl(self, action: dict[str, Any]) -> None:
    index = action["index"]
    self.apply_eat_choice(index)

def dispatch_action_impl(self, action: dict[str, Any]) -> None:
    action_type = action["type"]

    if action_type == "move":
        self._apply_move_action(action)
        return

    if action_type == "muzzle":
        self._apply_muzzle_action(action)
        return

    if action_type == "fire":
        self._apply_fire_action(action)
        return

    if action_type == "eat":
        self._apply_eat_action(action)
        return

    raise ValueError(f"未知动作类型：{action_type}")

def apply_action_impl(self, action: dict[str, Any]) -> None:
    if self.game_over:
        raise ValueError("游戏已结束，不能继续操作。")

    if not isinstance(action, dict):
        raise ValueError("action 必须是字典。")

    action_type = action.get("type")
    if action_type is None:
        raise ValueError("action 缺少 type 字段。")

    if not self.is_action_legal(action):
        raise ValueError(f"非法动作：{action}")

    previous_pending_auto_action = self.pending_auto_action
    self._dispatch_action(action)

    if self.pending_auto_action is previous_pending_auto_action:
        self.clear_pending_auto_action()

def try_apply_action_impl(self, action: dict[str, Any]) -> tuple[bool, str]:
    try:
        self.apply_action(action)
        return True, "ok"
    except Exception as e:
        return False, str(e)

def apply_action_with_snapshot_impl(
    self,
    action: dict[str, Any],
) -> dict[str, Any]:
    before = self.get_state_snapshot()
    self.apply_action(action)
    after = self.get_state_snapshot()

    return {
        "action": action,
        "action_text": self.action_to_command_text(action),
        "events": self.get_last_action_events(),
        "auto_action_messages": self.auto_action_messages.copy(),
        "before": before,
        "after": after,
    }

def try_apply_action_with_snapshot_impl(
    self,
    action: dict[str, Any],
) -> dict[str, Any]:
    try:
        result = self.apply_action_with_snapshot(action)
        return {
            "ok": True,
            "message": "ok",
            "result": result,
        }
    except Exception as e:
        return {
            "ok": False,
            "message": str(e),
            "result": None,
        }

def apply_single_legal_action_impl(self) -> dict[str, Any]:
    action = self.get_single_legal_action()
    if action is None:
        raise ValueError("当前不是唯一合法动作，无法自动执行。")

    self.apply_action(action)
    return action
`,
  "game_impl/cannon_mgmt.py": `# core/game_impl/cannon_mgmt.py
from __future__ import annotations

from typing import List

def remove_contained_old_cannons_impl(self, new_cannon) -> None:
    from core.cannon import cannon_contains

    remaining = []

    for old_cannon in self.fire_cannon_pool:
        if cannon_contains(new_cannon, old_cannon):
            self.debug(
                f"炮管集合更新: 新炮 {new_cannon.positions} 包含旧炮 {old_cannon.positions}，旧炮移出集合"
            )
        else:
            remaining.append(old_cannon)

    self.fire_cannon_pool = remaining

def get_all_cannons_impl(self) -> list:
    from core.cannon import find_all_cannons

    cannons = find_all_cannons(self.board)

    for cannon in cannons:
        self._apply_saved_mouth_to_cannon(cannon)

    return cannons

def apply_saved_mouth_to_cannon_impl(self, cannon):
    from core.cannon import cannon_signature

    sig = cannon_signature(cannon)

    if sig in self.cannon_mouth_map:
        cannon.mouth = self.cannon_mouth_map[sig]
        return cannon

    for pending in self.pending_muzzle_cannons:
        if cannon_signature(pending) == sig and pending.mouth is not None:
            cannon.mouth = pending.mouth
            return cannon

    return cannon

def initialize_fire_cannon_pool_impl(self) -> None:
    self.fire_cannon_pool = []

    for cannon in self.get_cannons_by_color(self.current_player):
        if cannon.mouth is not None:
            self.fire_cannon_pool.append(cannon)

def get_cannons_by_color_impl(self, color: str) -> list:
    return [c for c in self.get_all_cannons() if c.color == color]

def assign_muzzles_for_new_cannons_impl(self) -> None:
    from core.cannon import auto_determine_mouth, cannon_signature
    from core.record import player_name

    self.pending_muzzle_cannons = []
    auto_resolved_cannons = []

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

    self.record_new_cannons(auto_resolved_cannons)

def add_waiting_new_cannons_to_pool_impl(self) -> None:
    from core.cannon import cannon_signature

    if not self.waiting_new_pool_cannons:
        return

    for cannon in self.waiting_new_pool_cannons:
        self._apply_saved_mouth_to_cannon(cannon)

        self.remove_contained_old_cannons(cannon)

        sig = cannon_signature(cannon)
        exists = any(cannon_signature(old) == sig for old in self.fire_cannon_pool)

        if not exists:
            self.fire_cannon_pool.append(cannon)
            self.debug(
                f"炮管集合更新: 新炮 {cannon.positions} 加入当前炮管集合"
            )

    self.waiting_new_pool_cannons = []

def set_cannon_mouth_impl(self, index: int, direction_text: str) -> None:
    from core.cannon import cannon_signature
    from core.record import player_name

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
    self.clear_last_action_events()
    cannon.mouth = mouth
    self.cannon_mouth_map[cannon_signature(cannon)] = mouth
    self.add_last_action_event(
        self._make_event(
            "muzzle_set",
            index=index,
            direction=direction_text.lower(),
            cannon=self._serialize_cannon(cannon),
        )
    )

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
        self._record_phase_change_event()
        self.advance_turn()

def all_pending_muzzles_set_impl(self) -> bool:
    return all(c.mouth is not None for c in self.pending_muzzle_cannons)

def clear_pending_muzzles_impl(self) -> None:
    self.pending_muzzle_cannons = []

def get_phase_relevant_cannons_impl(self) -> list:
    return self.get_cannons_by_color(self.current_player)

def get_fireable_cannons_impl(self) -> list:
    return self.fire_cannon_pool.copy()`,
  "game_impl/clone.py": `# core/game_impl/clone.py
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
`,
  "game_impl/eat.py": `# core/game_impl/eat.py
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
`,
  "game_impl/fire.py": `# core/game_impl/fire.py
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
`,
  "game_impl/flow.py": `# core/game_impl/flow.py
from __future__ import annotations

from typing import List

def start_resolution_for_current_player_impl(self) -> None:
    from core.cannon import auto_determine_mouth, cannon_signature

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

    self._record_phase_change_event()

def has_pending_muzzle_choice_impl(self) -> bool:
    return bool(self.pending_muzzle_cannons)

def all_legal_moves_impl(self, color: str) -> List[str]:
    moves: List[str] = []

    for x, y in self.board.legal_place_positions(color):
        moves.append(f"move {x} {y}   [放置]")

    for x, y in self.board.legal_upgrade_positions(color):
        piece = self.board.get(x, y)
        if piece is not None:
            moves.append(f"move {x} {y}   [升级到{piece.level + 1}级]")

    return moves

def can_player_move_impl(self, color: str) -> bool:
    return bool(self.board.legal_place_positions(color) or self.board.legal_upgrade_positions(color))

def check_game_over_at_turn_start_impl(self) -> bool:
    if self.phase != "drop":
        return False

    if self.game_over:
        return True

    if not self.can_player_move(self.current_player):
        self.finish_game(reason="no_legal_move", winner=None)
        return True

    return False

def end_turn_impl(self) -> None:
    self.current_player = self.opponent(self.current_player)
    self.turn_number += 1

    self.clear_pending_auto_action()
    self.phase = "drop"
    self.pending_muzzle_cannons = []
    self.last_new_cannons = []
    self.fire_cannon_pool = []
    self.waiting_new_pool_cannons = []
    self.last_change_reached = {}
    self.last_fire_report_lines = []

def finish_full_round_impl(self) -> None:
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

    self.clear_pending_auto_action()
    self.pending_muzzle_cannons = []
    self.last_new_cannons = []
    self.fire_cannon_pool = []
    self.waiting_new_pool_cannons = []
    self.last_change_reached = {}
    self.last_fire_report_lines = []

    self._record_turn_change_event("full_round_finished")
    self._record_phase_change_event()

def advance_turn_impl(self) -> None:
    from core.record import format_cannon_for_record

    while True:
        if self.phase == "muzzle":
            return

        if self.phase == "fire":
            fireable = self.get_fireable_cannons()

            if len(fireable) >= 2:
                return

            if len(fireable) == 1:
                cannon = fireable[0]
                action = self.get_legal_fire_actions()[0]

                if self.last_new_cannons:
                    formed_text = "、".join(
                        format_cannon_for_record(c, self.cannon_record_style)
                        for c in self.last_new_cannons
                    )
                    message = (
                        f"本步形成{formed_text}\\n"
                        f"当前仅有 1 门可发射炮，可点击棋盘任意位置确认发射 "
                        f"{format_cannon_for_record(cannon, self.cannon_record_style)}"
                    )
                else:
                    message = (
                        f"当前仅有 1 门可发射炮，可点击棋盘任意位置确认发射 "
                        f"{format_cannon_for_record(cannon, self.cannon_record_style)}"
                    )

                self.set_pending_auto_action(action, message)
                return

            self.phase = "eat"
            continue

        if self.phase == "eat":
            targets = self.get_capturable_targets(self.current_player)

            if len(targets) >= 2:
                return

            if len(targets) == 1:
                x, y = targets[0]
                action = self.get_legal_eat_actions()[0]
                message = f"当前仅有 1 个可吃目标，可点击棋盘任意位置确认吃掉 ({x}, {y})"

                self.set_pending_auto_action(action, message)
                return

            self.chain_pass_count += 1

            if self.chain_pass_count >= 2:
                self.add_last_action_event(
                    self._make_event(
                        "auto_action",
                        action_type="finish_full_round",
                        reason="both_sides_cannot_continue",
                    )
                )
                self.finish_full_round()
                return

            previous_player = self.current_player
            self.current_player = self.opponent(self.current_player)

            self.add_last_action_event(
                self._make_event(
                    "auto_action",
                    action_type="switch_resolution_side",
                    reason="current_side_cannot_continue",
                    from_player=previous_player,
                    to_player=self.current_player,
                    to_player_name=self.current_player,
                )
            )

            self.start_resolution_for_current_player()
            continue

        return

def calculate_score_impl(self) -> tuple[int, int]:
    red_score = self.board.count_pieces("R")
    blue_score = self.board.count_pieces("B") + 9
    return red_score, blue_score

def determine_winner_by_score_impl(self) -> str | None:
    red_score, blue_score = self.calculate_score()

    if red_score > blue_score:
        return "R"
    if blue_score > red_score:
        return "B"
    return None

def finish_game_impl(
    self,
    reason: str,
    winner: str | None = None,
) -> None:
    self.game_over = True
    self.game_over_reason = reason

    if winner is None:
        winner = self.determine_winner_by_score()

    self.winner = winner
    self.phase = "drop"
    self.clear_pending_auto_action()

def finish_by_agreement_impl(self) -> None:
    self.finish_game(reason="agreement", winner=None)

def resign_impl(self, resigning_player: str | None = None) -> None:
    if resigning_player is None:
        resigning_player = self.current_player

    winner = self.opponent(resigning_player)
    self.finish_game(reason="resign", winner=winner)
`,
  "game_impl/legal.py": `# core/game_impl/legal.py
from __future__ import annotations

from typing import Any

def action_label_impl(self, action: dict[str, Any]) -> str:
    action_type = action["type"]

    if action_type == "move":
        x = action["x"]
        y = action["y"]
        if action["mode"] == "place":
            return f"move {x} {y} [放置]"
        return f"move {x} {y} [升级到{action['to_level']}级]"

    if action_type == "muzzle":
        return f"cannon {action['index']} {action['direction']}"

    if action_type == "fire":
        return f"fire {action['index']}"

    if action_type == "eat":
        return f"eat {action['index']}"

    return str(action)

def action_with_label_impl(self, action: dict[str, Any]) -> dict[str, Any]:
    result = action.copy()
    result["label"] = self._action_label(action)
    return result

def action_to_command_text_impl(self, action: dict[str, Any]) -> str:
    action_type = action["type"]

    if action_type == "move":
        return f"move {action['x']} {action['y']}"

    if action_type == "muzzle":
        return f"cannon {action['index']} {action['direction']}"

    if action_type == "fire":
        return f"fire {action['index']}"

    if action_type == "eat":
        return f"eat {action['index']}"

    raise ValueError(f"未知动作类型：{action_type}")

def legal_action_command_texts_impl(self) -> list[str]:
    return [
        self.action_to_command_text(action)
        for action in self.get_legal_actions()
    ]

def get_legal_drop_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for x, y in self.board.legal_place_positions(self.current_player):
        actions.append(
            self._action_with_label(
                {
                    "type": "move",
                    "mode": "place",
                    "x": x,
                    "y": y,
                    "player": self.current_player,
                    "phase": "drop",
                }
            )
        )

    for x, y in self.board.legal_upgrade_positions(self.current_player):
        piece = self.board.get(x, y)
        if piece is None:
            continue

        actions.append(
            self._action_with_label(
                {
                    "type": "move",
                    "mode": "upgrade",
                    "x": x,
                    "y": y,
                    "to_level": piece.level + 1,
                    "player": self.current_player,
                    "phase": "drop",
                }
            )
        )

    return actions

def get_legal_muzzle_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for i, cannon in enumerate(self.pending_muzzle_cannons, start=1):
        if cannon.direction == "H":
            directions = ["left", "right"]
        else:
            directions = ["up", "down"]

        for direction in directions:
            actions.append(
                self._action_with_label(
                    {
                        "type": "muzzle",
                        "index": i,
                        "direction": direction,
                        "player": self.current_player,
                        "phase": "muzzle",
                        "cannon": self._serialize_cannon(cannon),
                    }
                )
            )

    return actions

def get_legal_fire_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for i, cannon in enumerate(self.get_fireable_cannons(), start=1):
        actions.append(
            self._action_with_label(
                {
                    "type": "fire",
                    "index": i,
                    "player": self.current_player,
                    "phase": "fire",
                    "cannon": self._serialize_cannon(cannon),
                }
            )
        )

    return actions

def get_legal_eat_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    targets = self.get_capturable_targets(self.current_player)

    for i, (x, y) in enumerate(targets, start=1):
        actions.append(
            self._action_with_label(
                {
                    "type": "eat",
                    "index": i,
                    "x": x,
                    "y": y,
                    "player": self.current_player,
                    "phase": "eat",
                    "target_piece": self._serialize_piece_at(x, y),
                }
            )
        )

    return actions

def get_legal_actions_impl(self) -> list[dict[str, Any]]:
    if self.game_over:
        return []

    if self.phase == "drop":
        return self.get_legal_drop_actions()

    if self.phase == "muzzle":
        return self.get_legal_muzzle_actions()

    if self.phase == "fire":
        return self.get_legal_fire_actions()

    if self.phase == "eat":
        return self.get_legal_eat_actions()

    return []

def get_legal_actions_snapshot_impl(self) -> dict[str, Any]:
    actions = self.get_legal_actions()
    single_action = actions[0] if len(actions) == 1 else None

    return {
        "phase": self.phase,
        "current_player": self.current_player,
        "count": len(actions),
        "has_single_action": len(actions) == 1,
        "single_action": single_action,
        "actions": actions,
    }

def get_action_api_snapshot_impl(self) -> dict[str, Any]:
    return {
        "supports_structured_actions": True,
        "supports_apply_action": True,
        "supports_try_apply_action": True,
        "supports_apply_action_with_snapshot": True,
        "supports_try_apply_action_with_snapshot": True,
        "legal_action_count": len(self.get_legal_actions()),
        "has_single_legal_action": self.has_single_legal_action(),
        "single_legal_action": self.get_single_legal_action(),
        "supports_structured_events": True,
        "supports_auto_resolution_events": True,
        "supports_state_export": True,
        "supports_state_import": True,
    }

def has_single_legal_action_impl(self) -> bool:
    return len(self.get_legal_actions()) == 1

def get_single_legal_action_impl(self) -> dict[str, Any] | None:
    actions = self.get_legal_actions()
    if len(actions) != 1:
        return None
    return actions[0]

def is_action_legal_impl(self, action: dict[str, Any]) -> bool:
    legal_actions = self.get_legal_actions()

    for legal_action in legal_actions:
        if self._actions_equal_for_execution(action, legal_action):
            return True

    return False

def actions_equal_for_execution_impl(
    self,
    action1: dict[str, Any],
    action2: dict[str, Any],
) -> bool:
    keys_by_type = {
        "move": ["type", "mode", "x", "y"],
        "muzzle": ["type", "index", "direction"],
        "fire": ["type", "index"],
        "eat": ["type", "index"],
    }

    action_type_1 = action1.get("type")
    action_type_2 = action2.get("type")

    if action_type_1 != action_type_2:
        return False

    keys = keys_by_type.get(action_type_1)
    if keys is None:
        return False

    for key in keys:
        if action1.get(key) != action2.get(key):
            return False

    return True`,
  "game_impl/move.py": `# core/game_impl/move.py
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
`,
  "game_impl/report.py": `# core/game_impl/report.py
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
        f"第 {self.turn_number} 回合 | 当前行动方：{player_name(color)} | 当前阶段：{self.phase_name()}\\n"
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

    return "\\n".join(lines)


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
`,
  "models.py": `#models.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class Piece:
    color: str   # "R" or "B"
    level: int   # 1~5

    def short(self) -> str:
        return f"{self.color}{self.level}"

@dataclass
class Cannon:
    color: str
    level: int
    positions: Tuple[Tuple[int, int], ...]
    direction: str                 # "H" 或 "V"
    mouth: str | None = None       # 横向: "L"/"R"，纵向: "U"/"D"

    @property
    def length(self) -> int:
        return len(self.positions)

    def short(self) -> str:
        dir_name = "横向" if self.direction == "H" else "纵向"

        if self.mouth is None:
            mouth_name = "未定"
        elif self.mouth == "L":
            mouth_name = "左"
        elif self.mouth == "R":
            mouth_name = "右"
        elif self.mouth == "U":
            mouth_name = "上"
        else:
            mouth_name = "下"

        return (
            f"{self.color}{self.level}级{self.length}长炮"
            f"({dir_name}, 炮口:{mouth_name}) {list(self.positions)}"
        )`,
  "record.py": `#record.py
from __future__ import annotations

from typing import List

from core.board import Position
from core.models import Cannon

def player_name(color: str) -> str:
    return "红方" if color == "R" else "蓝方"

def format_pos(pos: Position) -> str:
    x, y = pos
    return f"({x}, {y})"

def mouth_text(mouth: str) -> str:
    mapping = {
        "L": "左",
        "R": "右",
        "U": "上",
        "D": "下",
    }
    return mapping.get(mouth, mouth)

def cannon_direction_text(direction: str) -> str:
    mapping = {
        "H": "横",
        "V": "纵",
    }
    return mapping.get(direction, direction)

def format_cannon_positions_for_record(cannon: Cannon) -> str:
    pos_texts = [format_pos(pos) for pos in cannon.positions]
    return "[" + ", ".join(pos_texts) + "]"

def format_cannon_tuple_record(cannon: Cannon) -> str:
    k = cannon.level
    n = len(cannon.positions)
    a_text = format_cannon_positions_for_record(cannon)
    dir_text = cannon_direction_text(cannon.direction)

    if cannon.mouth is None:
        mouth_name = "未定口"
    else:
        mouth_name = mouth_text(cannon.mouth)

    return f"({k}, {n}, {a_text}, {dir_text}, {mouth_name})"

def format_cannon_for_record(cannon: Cannon, style: int) -> str:
    if style == 1:
        return cannon.short()

    if style == 2:
        return format_cannon_tuple_record(cannon)

    return cannon.short()

def format_cannon_with_mouth_for_record(cannon: Cannon, style: int) -> str:
    base = format_cannon_for_record(cannon, style)

    if cannon.mouth is None:
        return base

    if style == 2:
        return base

    return f"{base}（{mouth_text(cannon.mouth)}口）"

def history_text(history: List[str]) -> str:
    if not history:
        return "当前还没有正式棋谱。"

    lines: List[str] = ["正式棋谱："]
    for i, item in enumerate(history, start=1):
        lines.append(f"  {i}. {item}")
    return "\\n".join(lines)

def debug_text(debug_log: List[str]) -> str:
    if not debug_log:
        return "当前还没有调试日志。"

    lines: List[str] = ["调试日志："]
    for i, item in enumerate(debug_log, start=1):
        lines.append(f"  {i}. {item}")
    return "\\n".join(lines)

def fire_report_text(last_fire_report_lines: List[str]) -> str:
    if not last_fire_report_lines:
        return "本次没有发炮明细。"
    return "\\n".join(last_fire_report_lines)

def piece_text(piece) -> str:
    if piece is None:
        return "空"
    return piece.short()

def new_cannons_report(cannons: List[Cannon]) -> str:
    if not cannons:
        return "本步未形成新炮。"

    lines: List[str] = ["新形成炮管："]

    for cannon in cannons:
        lines.append(f"  {player_name(cannon.color)} {cannon.short()}")

    return "\\n".join(lines)

def pending_muzzle_report(cannons: List[Cannon]) -> str:
    if not cannons:
        return "当前没有待选择炮口的新炮。"

    lines: List[str] = ["请为新炮选择炮口方向："]

    for i, cannon in enumerate(cannons, start=1):
        if cannon.direction == "H":
            hint = "left / right"
        else:
            hint = "up / down"

        lines.append(
            f"  {i}. {player_name(cannon.color)} {cannon.short()}  -> 可选: {hint}"
        )

    return "\\n".join(lines)

def fireable_report(player_color: str, cannons: List[Cannon]) -> str:
    lines: List[str] = []
    lines.append(f"{player_name(player_color)} 当前可发射炮管：")

    if not cannons:
        lines.append("  （暂无）")
    else:
        for i, cannon in enumerate(cannons, start=1):
            lines.append(f"  {i}. {cannon.short()}")

    return "\\n".join(lines)

def capturable_report(player_color: str, targets: List[tuple[int, int]], board) -> str:
    lines: List[str] = []
    lines.append(f"{player_name(player_color)} 当前可吃目标：")

    if not targets:
        lines.append("  （暂无）")
    else:
        for i, (x, y) in enumerate(targets, start=1):
            piece = board.get(x, y)
            if piece is not None:
                lines.append(f"  {i}. ({x}, {y}) {piece.short()}")

    return "\\n".join(lines)

def cannon_report(red_cannons: List[Cannon], blue_cannons: List[Cannon]) -> str:
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

    return "\\n".join(lines)`,
  "resolution.py": `#resolution.py
from __future__ import annotations

from typing import Dict, List

from core.board import Board, Position
from core.models import Cannon, Piece
from core.cannon import front_positions, cannon_positions_from_mouth

def signed_value(piece: Piece | None, firing_color: str) -> int:
    if piece is None:
        return 0

    if piece.color == firing_color:
        return piece.level

    return -piece.level

def piece_from_signed_value(
    value: int,
    firing_color: str,
    opponent_color: str,
) -> Piece | None:
    if value == 0:
        return None

    level = min(5, abs(value))

    if value > 0:
        return Piece(firing_color, level)

    return Piece(opponent_color, level)

def collect_front_updates(
    board: Board,
    cannon: Cannon,
    firing_color: str,
    opponent_color: str,
) -> Dict[Position, Piece | None]:
    updates: Dict[Position, Piece | None] = {}

    for pos in front_positions(board, cannon):
        x, y = pos
        old_piece = board.get(x, y)
        old_value = signed_value(old_piece, firing_color)
        new_value = old_value + cannon.level
        new_piece = piece_from_signed_value(new_value, firing_color, opponent_color)
        updates[pos] = new_piece

    return updates

def apply_piece_updates(
    board: Board,
    updates: Dict[Position, Piece | None],
) -> None:
    for (x, y), piece in updates.items():
        board.set(x, y, piece)

def collect_body_updates(
    board: Board,
    cannon: Cannon,
) -> Dict[Position, Piece | None]:
    updates: Dict[Position, Piece | None] = {}

    positions_from_mouth = cannon_positions_from_mouth(cannon)

    for distance, (x, y) in enumerate(positions_from_mouth):
        if distance % 2 != 1:
            continue

        piece = board.get(x, y)

        if piece is None:
            continue

        if piece.color != cannon.color:
            continue

        new_level = min(5, piece.level + 1)
        updates[(x, y)] = Piece(piece.color, new_level)

    return updates

def merge_reached_from_updates(
    reached: Dict[Position, tuple[str, int]],
    updates: Dict[Position, Piece | None],
) -> None:
    for pos, piece in updates.items():
        if piece is not None:
            reached[pos] = (piece.color, piece.level)`,
  "save_io.py": `# core/save_io.py
from __future__ import annotations

import json

from core.game import Game

def save_game_to_file(game: Game, filename: str) -> None:
    data = game.export_full_state()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_game_from_file(filename: str) -> Game:
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Game.from_exported_state(data)

def export_record_to_file(game: Game, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        if game.history:
            f.write("\\n".join(game.history))
        else:
            f.write("（暂无棋谱）")
`,
  "state_io.py": `#state_io.py
from __future__ import annotations

from copy import deepcopy
from typing import Any, TYPE_CHECKING

from core.cannon import cannon_signature
from core.models import Cannon, Piece
from core.record import format_cannon_for_record, player_name

if TYPE_CHECKING:
    from core.game import Game

def serialize_piece_at(game: "Game", x: int, y: int) -> dict[str, Any] | None:
    piece = game.board.get(x, y)
    if piece is None:
        return None

    return {
        "color": piece.color,
        "level": piece.level,
        "short": piece.short(),
    }

def serialize_cannon(game: "Game", cannon: Cannon) -> dict[str, Any]:
    return {
        "color": cannon.color,
        "level": cannon.level,
        "length": cannon.length,
        "direction": cannon.direction,
        "mouth": cannon.mouth,
        "positions": [
            {"x": x, "y": y}
            for x, y in cannon.positions
        ],
        "signature": list(cannon_signature(cannon)),
        "short": cannon.short(),
        "record_text": format_cannon_for_record(cannon, game.cannon_record_style),
    }

def get_board_snapshot(game: "Game") -> list[list[dict[str, Any] | None]]:
    rows: list[list[dict[str, Any] | None]] = []

    for y in range(1, game.board.SIZE + 1):
        row: list[dict[str, Any] | None] = []

        for x in range(1, game.board.SIZE + 1):
            row.append(serialize_piece_at(game, x, y))

        rows.append(row)

    return rows

def get_cannon_snapshot(game: "Game", cannons: list[Cannon]) -> list[dict[str, Any]]:
    return [serialize_cannon(game, cannon) for cannon in cannons]

def get_all_cannons_snapshot(game: "Game") -> dict[str, list[dict[str, Any]]]:
    red_cannons = game.get_cannons_by_color("R")
    blue_cannons = game.get_cannons_by_color("B")

    return {
        "R": get_cannon_snapshot(game, red_cannons),
        "B": get_cannon_snapshot(game, blue_cannons),
    }

def get_phase_snapshot(game: "Game") -> dict[str, Any]:
    return {
        "phase": game.phase,
        "phase_name": game.phase_name(),
        "current_player": game.current_player,
        "current_player_name": player_name(game.current_player),
        "turn_number": game.turn_number,
        "round_drop_player": game.round_drop_player,
        "chain_pass_count": game.chain_pass_count,
        "has_pending_muzzle_choice": game.has_pending_muzzle_choice(),
        "game_over": game.game_over,
        "winner": game.winner,
    }

def get_interaction_snapshot(game: "Game") -> dict[str, Any]:
    fireable = game.get_fireable_cannons()
    capturable = game.get_capturable_targets(game.current_player)

    return {
        "last_new_cannons": get_cannon_snapshot(game, game.last_new_cannons),
        "pending_muzzle_cannons": get_cannon_snapshot(game, game.pending_muzzle_cannons),
        "fire_cannon_pool": get_cannon_snapshot(game, game.fire_cannon_pool),
        "fireable_cannons": get_cannon_snapshot(game, fireable),
        "capturable_targets": [
            {
                "x": x,
                "y": y,
                "piece": serialize_piece_at(game, x, y),
            }
            for x, y in capturable
        ],
        "last_change_reached": [
            {
                "x": x,
                "y": y,
                "color": color,
                "level": level,
            }
            for (x, y), (color, level) in game.last_change_reached.items()
        ],
    }

def get_log_snapshot(game: "Game") -> dict[str, Any]:
    return {
        "history": game.history.copy(),
        "debug_log": game.debug_log.copy(),
        "command_log": game.command_log.copy(),
        "last_fire_report_lines": game.last_fire_report_lines.copy(),
        "auto_action_messages": game.auto_action_messages.copy(),
        "last_action_events": game.get_last_action_events(),
    }

def get_drop_legal_snapshot(game: "Game") -> dict[str, Any]:
    place_positions = game.board.legal_place_positions(game.current_player)
    upgrade_positions = game.board.legal_upgrade_positions(game.current_player)

    return {
        "place_positions": [
            {"x": x, "y": y}
            for x, y in place_positions
        ],
        "upgrade_positions": [
            {
                "x": x,
                "y": y,
                "to_level": game.board.get(x, y).level + 1,
            }
            for x, y in upgrade_positions
            if game.board.get(x, y) is not None
        ],
        "all_legal_moves_text": game.all_legal_moves(game.current_player),
    }

def get_state_snapshot(game: "Game") -> dict[str, Any]:
    red_score, blue_score = game.calculate_score()

    return {
        "phase_info": get_phase_snapshot(game),
        "board": get_board_snapshot(game),
        "cannons": get_all_cannons_snapshot(game),
        "interaction": get_interaction_snapshot(game),
        "drop_legal": get_drop_legal_snapshot(game),
        "legal_actions": game.get_legal_actions_snapshot(),
        "logs": get_log_snapshot(game),
        "score": {
            "R": red_score,
            "B": blue_score,
        },
        "cannon_record_style": game.cannon_record_style,
        "action_api": game.get_action_api_snapshot(),
    }

def export_board_state(game: "Game") -> list[list[dict[str, Any] | None]]:
    return get_board_snapshot(game)

def export_cannon_list(game: "Game", cannons: list[Cannon]) -> list[dict[str, Any]]:
    return [serialize_cannon(game, cannon) for cannon in cannons]

def export_full_state(game: "Game") -> dict[str, Any]:
    return {
        "board": export_board_state(game),
        "phase": game.phase,
        "current_player": game.current_player,
        "turn_number": game.turn_number,
        "round_drop_player": game.round_drop_player,
        "chain_pass_count": game.chain_pass_count,
        "game_over": game.game_over,
        "winner": game.winner,
        "game_over_reason": game.game_over_reason,
        "cannon_record_style": game.cannon_record_style,
        "last_new_cannons": export_cannon_list(game, game.last_new_cannons),
        "pending_muzzle_cannons": export_cannon_list(game, game.pending_muzzle_cannons),
        "waiting_new_pool_cannons": export_cannon_list(game, game.waiting_new_pool_cannons),
        "fire_cannon_pool": export_cannon_list(game, game.fire_cannon_pool),
        "cannon_mouth_map": [
            {
                "signature": list(sig),
                "mouth": mouth,
            }
            for sig, mouth in game.cannon_mouth_map.items()
        ],
        "last_change_reached": [
            {
                "x": x,
                "y": y,
                "color": color,
                "level": level,
            }
            for (x, y), (color, level) in game.last_change_reached.items()
        ],
        "history": game.history.copy(),
        "debug_log": game.debug_log.copy(),
        "command_log": game.command_log.copy(),
        "last_fire_report_lines": game.last_fire_report_lines.copy(),
        "auto_action_messages": game.auto_action_messages.copy(),
        "pending_auto_action": deepcopy(game.pending_auto_action),
        "pending_auto_message": game.pending_auto_message,
        "last_action_events": game.get_last_action_events(),
    }

def deserialize_piece_data(data: dict[str, Any] | None) -> Piece | None:
    if data is None:
        return None
    return Piece(data["color"], data["level"])

def deserialize_cannon_data(data: dict[str, Any]) -> Cannon:
    return Cannon(
        color=data["color"],
        level=data["level"],
        positions=tuple((item["x"], item["y"]) for item in data["positions"]),
        direction=data["direction"],
        mouth=data["mouth"],
    )

def import_full_state(game: "Game", data: dict[str, Any]) -> None:
    for y, row in enumerate(data["board"], start=1):
        for x, cell in enumerate(row, start=1):
            game.board.set(x, y, deserialize_piece_data(cell))

    game.phase = data["phase"]
    game.current_player = data["current_player"]
    game.turn_number = data["turn_number"]
    game.round_drop_player = data["round_drop_player"]
    game.chain_pass_count = data["chain_pass_count"]
    game.game_over = data["game_over"]
    game.winner = data["winner"]
    game.game_over_reason = data.get("game_over_reason")
    game.cannon_record_style = data["cannon_record_style"]

    game.last_new_cannons = [
        deserialize_cannon_data(item)
        for item in data["last_new_cannons"]
    ]
    game.pending_muzzle_cannons = [
        deserialize_cannon_data(item)
        for item in data["pending_muzzle_cannons"]
    ]
    game.waiting_new_pool_cannons = [
        deserialize_cannon_data(item)
        for item in data["waiting_new_pool_cannons"]
    ]
    game.fire_cannon_pool = [
        deserialize_cannon_data(item)
        for item in data["fire_cannon_pool"]
    ]

    game.cannon_mouth_map = {}
    for item in data["cannon_mouth_map"]:
        sig = item["signature"]
        restored_sig = (
            sig[0],
            sig[1],
            tuple(tuple(pos) for pos in sig[2]),
            sig[3],
        )
        game.cannon_mouth_map[restored_sig] = item["mouth"]

    game.last_change_reached = {
        (item["x"], item["y"]): (item["color"], item["level"])
        for item in data["last_change_reached"]
    }

    game.history = data["history"].copy()
    game.debug_log = data["debug_log"].copy()
    game.command_log = data["command_log"].copy()
    game.last_fire_report_lines = data["last_fire_report_lines"].copy()
    game.auto_action_messages = data["auto_action_messages"].copy()
    game.pending_auto_action = deepcopy(data.get("pending_auto_action"))
    game.pending_auto_message = data.get("pending_auto_message", "")
    game.last_action_events = [event.copy() for event in data["last_action_events"]]

    game.undo_stack = []

def from_exported_state(data: dict[str, Any]) -> "Game":
    from core.game import Game

    game = Game()
    import_full_state(game, data)
    return game
`,
  "undo.py": `#undo.py
from __future__ import annotations

from copy import deepcopy
from typing import List

from core.models import Piece, Cannon

def copy_board_grid(board_grid: list[list[Piece | None]]) -> list[list[Piece | None]]:
    copied: list[list[Piece | None]] = []

    for row in board_grid:
        new_row: list[Piece | None] = []
        for piece in row:
            if piece is None:
                new_row.append(None)
            else:
                new_row.append(Piece(piece.color, piece.level))
        copied.append(new_row)

    return copied

def copy_cannon(cannon: Cannon) -> Cannon:
    copied = Cannon(
        color=cannon.color,
        level=cannon.level,
        positions=tuple(cannon.positions),
        direction=cannon.direction,
    )
    copied.mouth = cannon.mouth
    return copied

def copy_cannon_list(cannons: List[Cannon]) -> List[Cannon]:
    return [copy_cannon(c) for c in cannons]

def snapshot_state(game) -> dict:
    return {
        "board_grid": copy_board_grid(game.board.grid),
        "current_player": game.current_player,
        "turn_number": game.turn_number,
        "history": game.history.copy(),
        "debug_log": game.debug_log.copy(),
        "command_log": game.command_log.copy(),
        "game_over": game.game_over,
        "winner": game.winner,
        "game_over_reason": game.game_over_reason,
        "last_new_cannons": copy_cannon_list(game.last_new_cannons),
        "pending_muzzle_cannons": copy_cannon_list(game.pending_muzzle_cannons),
        "last_fire_report_lines": game.last_fire_report_lines.copy(),
        "auto_action_messages": game.auto_action_messages.copy(),
        "last_action_events": deepcopy(game.last_action_events),
        "last_change_reached": game.last_change_reached.copy(),
        "cannon_mouth_map": game.cannon_mouth_map.copy(),
        "fire_cannon_pool": copy_cannon_list(game.fire_cannon_pool),
        "waiting_new_pool_cannons": copy_cannon_list(game.waiting_new_pool_cannons),
        "pending_auto_action": deepcopy(game.pending_auto_action),
        "pending_auto_message": game.pending_auto_message,
        "phase": game.phase,
        "round_drop_player": game.round_drop_player,
        "chain_pass_count": game.chain_pass_count,
        "cannon_record_style": game.cannon_record_style,
    }

def restore_state(game, snapshot: dict) -> None:
    game.board.grid = snapshot["board_grid"]
    game.current_player = snapshot["current_player"]
    game.turn_number = snapshot["turn_number"]
    game.history = snapshot["history"]
    game.debug_log = snapshot["debug_log"]
    game.command_log = snapshot["command_log"]
    game.game_over = snapshot["game_over"]
    game.winner = snapshot["winner"]
    game.game_over_reason = snapshot["game_over_reason"]
    game.last_new_cannons = snapshot["last_new_cannons"]
    game.pending_muzzle_cannons = snapshot["pending_muzzle_cannons"]
    game.last_fire_report_lines = snapshot["last_fire_report_lines"]
    game.auto_action_messages = snapshot["auto_action_messages"]
    game.last_action_events = snapshot["last_action_events"]
    game.last_change_reached = snapshot["last_change_reached"]
    game.cannon_mouth_map = snapshot["cannon_mouth_map"]
    game.fire_cannon_pool = snapshot["fire_cannon_pool"]
    game.waiting_new_pool_cannons = snapshot["waiting_new_pool_cannons"]
    game.pending_auto_action = snapshot["pending_auto_action"]
    game.pending_auto_message = snapshot["pending_auto_message"]
    game.phase = snapshot["phase"]
    game.round_drop_player = snapshot["round_drop_player"]
    game.chain_pass_count = snapshot["chain_pass_count"]
    game.cannon_record_style = snapshot["cannon_record_style"]
`,
};

export default CORE_MODULES;
