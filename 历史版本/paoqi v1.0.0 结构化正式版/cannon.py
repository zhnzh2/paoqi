#cannon
from __future__ import annotations

from typing import List, Tuple

from board import Board, Position
from models import Cannon, Piece


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

    return result