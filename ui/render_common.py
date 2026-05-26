#ui/render_common.py
from __future__ import annotations

from typing import Any
import pygame

from ui.constants import *
from ui.scale import ui

def make_fonts() -> dict[str, pygame.font.Font]:
    return {
        "title": ui.font("microsoftyaheiui", 63, bold=True),
        "heading": ui.font("microsoftyaheiui", 45, bold=True),
        "body": ui.font("microsoftyaheiui", 30),
        "small": ui.font("microsoftyaheiui", 24),
        "piece": ui.font("arial", 42, bold=True),
    }

def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    x: int,
    y: int,
) -> None:
    img = font.render(text, True, color)
    surface.blit(img, (x, y))


def font_h(font: pygame.font.Font) -> int:
    return font.get_height()


def text_block_h(font: pygame.font.Font, lines: int = 1, gap: int = 0) -> int:
    if lines <= 0:
        return 0
    return lines * font_h(font) + (lines - 1) * gap


def visible_line_count(text: str, max_lines: int | None = None) -> int:
    lines = text.splitlines() if text else [""]
    count = len(lines)
    if max_lines is not None:
        count = min(count, max_lines)
    return max(1, count)


def multiline_block_height(
    text: str,
    font: pygame.font.Font,
    line_gap: int,
    max_lines: int | None = None,
) -> int:
    return text_block_h(font, visible_line_count(text, max_lines=max_lines), line_gap)


def draw_multiline_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    x: int,
    y: int,
    line_gap: int = 0,
    max_lines: int | None = None,
) -> None:
    lines = text.splitlines() if text else [""]
    if max_lines is not None:
        lines = lines[:max_lines]

    yy = y
    for line in lines:
        draw_text(surface, line, font, color, x, yy)
        yy += font_h(font) + line_gap


def draw_button(
    surface: pygame.Surface,
    text: str,
    rect: pygame.Rect,
    fonts: dict[str, pygame.font.Font],
    hovered: bool = False,
) -> None:
    bg = BUTTON_HOVER_BG if hovered else BUTTON_BG

    pygame.draw.rect(surface, bg, rect, border_radius=10)
    pygame.draw.rect(surface, BUTTON_BORDER, rect, 2, border_radius=10)

    txt = fonts["small"].render(text, True, BUTTON_TEXT)
    txt_rect = txt.get_rect(center=rect.center)
    surface.blit(txt, txt_rect)


def draw_danger_button(
    surface: pygame.Surface,
    text: str,
    rect: pygame.Rect,
    fonts: dict[str, pygame.font.Font],
    hovered: bool = False,
) -> None:
    bg = DANGER_BUTTON_BG
    border = DANGER_BUTTON_BORDER

    pygame.draw.rect(surface, bg, rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, 2, border_radius=10)

    txt = fonts["small"].render(text, True, DANGER_BUTTON_TEXT)
    txt_rect = txt.get_rect(center=rect.center)
    surface.blit(txt, txt_rect)


def draw_card_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    bg_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
) -> None:
    shadow = rect.move(ui.x(CARD_SHADOW_OFFSET), ui.y(CARD_SHADOW_OFFSET))
    shadow_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
    shadow_surf.fill(MODAL_SHADOW)
    surface.blit(shadow_surf, shadow.topleft)

    pygame.draw.rect(surface, bg_color, rect, border_radius=ui.u(CARD_RADIUS))
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=ui.u(CARD_RADIUS))