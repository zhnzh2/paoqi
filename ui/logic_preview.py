#ui/logic_preview.py
from __future__ import annotations

from core.game import Game
from ui.controller import (
    find_drop_action_by_cell,
    find_eat_action_by_cell,
    find_fire_actions_by_cell,
    find_muzzle_actions_by_endpoint,
)


def compute_preview_board_data(
    game: Game,
    legal_actions: list[dict],
    hovered_cell: tuple[int, int] | None,
    preview_drop_enabled: bool,
    preview_eat_enabled: bool,
    preview_fire_enabled: bool,
) -> list[list[dict | None]] | None:
    if game.game_over:
        return None

    if game.has_pending_auto_action():
        return None

    if hovered_cell is None:
        return None

    preview_action = None
    hx, hy = hovered_cell

    if game.phase == "drop" and preview_drop_enabled:
        preview_action = find_drop_action_by_cell(legal_actions, hx, hy)

    elif game.phase == "eat" and preview_eat_enabled:
        preview_action = find_eat_action_by_cell(legal_actions, hx, hy)

    elif game.phase == "muzzle" and preview_fire_enabled:
        muzzle_actions = find_muzzle_actions_by_endpoint(legal_actions, hx, hy)
        if len(muzzle_actions) == 1:
            preview_action = muzzle_actions[0]

    elif game.phase == "fire" and preview_fire_enabled:
        fire_actions = find_fire_actions_by_cell(legal_actions, hx, hy)
        if len(fire_actions) == 1:
            preview_action = fire_actions[0]

    if preview_action is None:
        return None

    try:
        preview_game = game.clone()
        ok, _ = preview_game.try_apply_action(preview_action)
        if ok:
            return preview_game.get_board_snapshot()
    except Exception:
        return None

    return None