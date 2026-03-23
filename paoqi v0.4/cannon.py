from __future__ import annotations

from typing import List, Tuple

from board import Board
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