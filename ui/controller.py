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

def find_eat_action_by_cell(
    legal_actions: list[dict[str, Any]],
    x: int,
    y: int,
) -> dict[str, Any] | None:
    for action in legal_actions:
        if action.get("type") != "eat":
            continue
        if action.get("x") == x and action.get("y") == y:
            return action
    return None


def find_fire_actions_by_cell(
    legal_actions: list[dict[str, Any]],
    x: int,
    y: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for action in legal_actions:
        if action.get("type") != "fire":
            continue

        cannon = action.get("cannon")
        if not isinstance(cannon, dict):
            continue

        positions = cannon.get("positions", [])
        for pos in positions:
            px = pos.get("x")
            py = pos.get("y")
            if px == x and py == y:
                result.append(action)
                break

    return result


def get_hovered_drop_highlights(
    legal_actions: list[dict[str, Any]],
    hovered_cell: tuple[int, int] | None,
) -> dict[tuple[int, int], str]:
    if hovered_cell is None:
        return {}

    x, y = hovered_cell
    action = find_drop_action_by_cell(legal_actions, x, y)
    if action is None:
        return {}

    mode = action.get("mode")
    if mode not in {"place", "upgrade"}:
        return {}

    return {(x, y): mode}


def get_hovered_eat_cells(
    legal_actions: list[dict[str, Any]],
    hovered_cell: tuple[int, int] | None,
) -> list[tuple[int, int]]:
    if hovered_cell is None:
        return []

    x, y = hovered_cell
    action = find_eat_action_by_cell(legal_actions, x, y)
    if action is None:
        return []

    return [(x, y)]

def get_hovered_fire_cannons(
    legal_actions: list[dict[str, Any]],
    hovered_cell: tuple[int, int] | None,
) -> list[dict[str, Any]]:
    if hovered_cell is None:
        return []

    x, y = hovered_cell

    fire_actions = find_fire_actions_by_cell(legal_actions, x, y)
    if fire_actions:
        return fire_actions

    return find_muzzle_actions_by_cell(legal_actions, x, y)

def find_muzzle_actions_by_cell(
    legal_actions: list[dict[str, Any]],
    x: int,
    y: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for action in legal_actions:
        if action.get("type") != "muzzle":
            continue

        cannon = action.get("cannon")
        if not isinstance(cannon, dict):
            continue

        positions = cannon.get("positions", [])
        if not positions:
            continue

        # 任意炮身格悬停都算命中，用于“进一步高亮”
        for pos in positions:
            px = pos.get("x")
            py = pos.get("y")
            if px == x and py == y:
                result.append(action)
                break

    return result

def find_muzzle_actions_by_endpoint(
    legal_actions: list[dict[str, Any]],
    x: int,
    y: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for action in legal_actions:
        if action.get("type") != "muzzle":
            continue

        cannon = action.get("cannon")
        if not isinstance(cannon, dict):
            continue

        positions = cannon.get("positions", [])
        if not positions:
            continue

        xs = [pos.get("x") for pos in positions if isinstance(pos.get("x"), int)]
        ys = [pos.get("y") for pos in positions if isinstance(pos.get("y"), int)]
        if not xs or not ys:
            continue

        direction = action.get("direction")

        if direction == "left":
            target = (min(xs), ys[0])
        elif direction == "right":
            target = (max(xs), ys[0])
        elif direction == "up":
            target = (xs[0], min(ys))
        elif direction == "down":
            target = (xs[0], max(ys))
        else:
            continue

        if target == (x, y):
            result.append(action)

    return result