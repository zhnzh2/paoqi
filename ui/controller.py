# ui/controller.py

from __future__ import annotations

from typing import Any

from ui.constants import (
    BOARD_ORIGIN_X,
    BOARD_ORIGIN_Y,
    BOARD_SIZE,
    BOARD_CELL,
    LOGICAL_WIDTH,
    LOGICAL_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)
from ui.scale import ui

def window_to_logical(mx: int, my: int) -> tuple[int, int]:
    lx = int(mx * LOGICAL_WIDTH / WINDOW_WIDTH)
    ly = int(my * LOGICAL_HEIGHT / WINDOW_HEIGHT)
    return lx, ly

def pixel_to_board(mx: int, my: int) -> tuple[int, int] | None:
    mx, my = window_to_logical(mx, my)

    origin_x = ui.x(BOARD_ORIGIN_X)
    origin_y = ui.y(BOARD_ORIGIN_Y)
    cell = ui.u(BOARD_CELL)

    rel_x = mx - origin_x
    rel_y = my - origin_y

    if rel_x < 0 or rel_y < 0:
        return None

    col = rel_x // cell
    row = rel_y // cell

    if not (0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE):
        return None

    return int(col + 1), int(row + 1)

def find_drop_action_by_cell(legal_actions: list[dict[str, Any]], x: int, y: int) -> dict[str, Any] | None:
    """
    在落子阶段，从所有合法动作里找到点击格子对应的 move 动作。
    优先返回精确匹配的那个动作。
    """
    for action in legal_actions:
        if action.get("type") != "move":
            continue
        if action.get("x") == x and action.get("y") == y:
            return action
    return None


def get_legal_cell_highlights(legal_actions: list[dict[str, Any]]) -> dict[tuple[int, int], str]:
    """
    返回每个格子的高亮类型：
    - place
    - upgrade
    """
    result: dict[tuple[int, int], str] = {}

    for action in legal_actions:
        if action.get("type") != "move":
            continue

        x = action.get("x")
        y = action.get("y")
        mode = action.get("mode")

        if isinstance(x, int) and isinstance(y, int):
            result[(x, y)] = mode

    return result

def get_capturable_highlights(legal_actions: list[dict[str, Any]]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []

    for action in legal_actions:
        if action.get("type") != "eat":
            continue

        x = action.get("x")
        y = action.get("y")
        if isinstance(x, int) and isinstance(y, int):
            result.append((x, y))

    return result

def get_fire_cannon_highlights(
    legal_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    返回当前可发射/可选炮口动作里涉及的炮管数据。
    每个元素大致长这样：
    {
        "type": "fire" 或 "muzzle",
        "index": 1,
        "cannon": {...}
    }
    """
    result: list[dict[str, Any]] = []

    for action in legal_actions:
        if action.get("type") not in {"fire", "muzzle"}:
            continue

        cannon = action.get("cannon")
        if isinstance(cannon, dict):
            result.append(
                {
                    "type": action.get("type"),
                    "index": action.get("index"),
                    "direction": action.get("direction"),
                    "cannon": cannon,
                    "label": action.get("label", ""),
                }
            )

    return result