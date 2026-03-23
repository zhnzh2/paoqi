#board.py
from __future__ import annotations

from typing import List, Optional, Tuple

from models import Piece


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
        return "\n".join(lines)
    
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

        return total