#models.py
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
        )