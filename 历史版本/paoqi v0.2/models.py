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
    color: str                     # "R" or "B"
    level: int                     # 1~4
    positions: Tuple[Tuple[int, int], ...]
    direction: str                 # "H" 或 "V"

    @property
    def length(self) -> int:
        return len(self.positions)

    def short(self) -> str:
        dir_name = "横向" if self.direction == "H" else "纵向"
        return f"{self.color}{self.level}级{self.length}长炮({dir_name}) {list(self.positions)}"