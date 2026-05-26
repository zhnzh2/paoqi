#ui/logic_click.py
from __future__ import annotations

from core.game import Game
from ui.controller import (
    find_drop_action_by_cell,
    find_eat_action_by_cell,
    find_fire_actions_by_cell,
    find_muzzle_actions_by_endpoint,
)


def execute_action(game: Game, action: dict) -> tuple[str, bool]:
    result = game.try_apply_action_with_snapshot(action)
    if result["ok"]:
        standardized = game.action_to_command_text(action)
        game.log_command(standardized)

        payload = result.get("result", {})
        return f"操作成功：{payload.get('action_text', standardized)}", False

    return f"操作失败：{result['message']}", True


def handle_pending_auto_action_click(game: Game) -> tuple[bool, str, bool]:
    if not game.has_pending_auto_action():
        return False, "", False

    pending = game.pending_auto_action
    if pending is None:
        return False, "", False

    message, is_error = execute_action(game, pending)
    return True, message, is_error


def handle_board_phase_click(
    game: Game,
    legal_actions: list[dict],
    x: int,
    y: int,
) -> tuple[bool, str, bool]:
    if game.phase == "drop":
        action = find_drop_action_by_cell(legal_actions, x, y)
        if action is None:
            return True, f"({x}, {y}) 不是当前合法落子位置。", True
        return True, *execute_action(game, action)

    if game.phase == "eat":
        action = find_eat_action_by_cell(legal_actions, x, y)
        if action is None:
            return True, f"({x}, {y}) 不是当前可吃目标。", True
        return True, *execute_action(game, action)

    if game.phase == "muzzle":
        muzzle_actions = find_muzzle_actions_by_endpoint(legal_actions, x, y)

        if len(muzzle_actions) == 0:
            return True, f"({x}, {y}) 不是可选炮口端点。", True

        if len(muzzle_actions) == 1:
            return True, *execute_action(game, muzzle_actions[0])

        return True, f"({x}, {y}) 对应多个炮口方向，暂不自动选择。", True

    if game.phase == "fire":
        fire_actions = find_fire_actions_by_cell(legal_actions, x, y)

        if len(fire_actions) == 0:
            return True, f"({x}, {y}) 不属于当前可发射炮管。", True

        if len(fire_actions) == 1:
            return True, *execute_action(game, fire_actions[0])

        return True, f"({x}, {y}) 同时属于 {len(fire_actions)} 门可发射炮，暂不自动选择。", True

    return True, f"当前阶段是 {game.phase_name()}。\n该阶段暂不支持直接点棋盘执行。", True