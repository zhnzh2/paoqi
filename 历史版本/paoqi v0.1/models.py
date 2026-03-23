from dataclasses import dataclass


@dataclass
class Piece:
    color: str   # "R" or "B"
    level: int   # 1~5

    def short(self) -> str:
        return f"{self.color}{self.level}"