#scale.py

# ui/scale.py

from __future__ import annotations

import pygame

from ui.constants import (
    DESIGN_WIDTH,
    DESIGN_HEIGHT,
    LOGICAL_WIDTH,
    LOGICAL_HEIGHT,
)


class UIScaler:
    def __init__(self) -> None:
        self.sx = LOGICAL_WIDTH / DESIGN_WIDTH
        self.sy = LOGICAL_HEIGHT / DESIGN_HEIGHT
        self.su = min(self.sx, self.sy)

    def x(self, value: int | float) -> int:
        return int(round(value * self.sx))

    def y(self, value: int | float) -> int:
        return int(round(value * self.sy))

    def u(self, value: int | float) -> int:
        return int(round(value * self.su))

    def pt(self, x: int | float, y: int | float) -> tuple[int, int]:
        return self.x(x), self.y(y)

    def rect(self, x: int | float, y: int | float, w: int | float, h: int | float) -> pygame.Rect:
        return pygame.Rect(self.x(x), self.y(y), self.x(w), self.y(h))

    def font(self, name: str, size: int, bold: bool = False) -> pygame.font.Font:
        return pygame.font.SysFont(name, self.u(size), bold=bold)


ui = UIScaler()