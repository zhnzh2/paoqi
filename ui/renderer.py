# ui/renderer.py

from __future__ import annotations

import pygame
import pygame.gfxdraw
from typing import Any

from ui.constants import *
from ui.scale import ui

def make_fonts() -> dict[str, pygame.font.Font]:
    return {
        "title": ui.font("microsoftyaheiui", 40, bold=True),
        "heading": ui.font("microsoftyaheiui", 30, bold=True),
        "body": ui.font("microsoftyaheiui", 26),
        "small": ui.font("microsoftyaheiui", 22),
        "piece": ui.font("arial", 36, bold=True),
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
    return font.get_linesize()


def text_block_h(font: pygame.font.Font, lines: int = 1, gap: int = 0) -> int:
    if lines <= 0:
        return 0
    return lines * font.get_linesize() + (lines - 1) * gap

def visible_line_count(text: str, max_lines: int | None = None) -> int:
    lines = text.splitlines() if text else []
    if max_lines is not None:
        lines = lines[:max_lines]
    return max(1, len(lines))


def multiline_block_height(
    text: str,
    font: pygame.font.Font,
    line_gap: int = 0,
    max_lines: int | None = None,
) -> int:
    return text_block_h(
        font,
        lines=visible_line_count(text, max_lines=max_lines),
        gap=line_gap,
    )

def draw_multiline_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    x: int,
    y: int,
    line_gap: int = 6,
    max_lines: int | None = None,
) -> None:
    lines = text.splitlines() if text else []
    if max_lines is not None:
        lines = lines[:max_lines]

    cy = y
    for line in lines:
        img = font.render(line, True, color)
        surface.blit(img, (x, cy))
        cy += img.get_height() + line_gap

def aa_filled_circle(
    surface: pygame.Surface,
    x: int,
    y: int,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    pygame.gfxdraw.filled_circle(surface, x, y, radius, color)
    pygame.gfxdraw.aacircle(surface, x, y, radius, color)


def aa_circle_outline(
    surface: pygame.Surface,
    x: int,
    y: int,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    pygame.gfxdraw.aacircle(surface, x, y, radius, color)

def draw_piece_disc(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    light_color: tuple[int, int, int],
    dark_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
) -> None:
    cx, cy = center

    # 外层深色
    aa_filled_circle(surface, cx, cy, radius, dark_color)

    # 中层主色
    aa_filled_circle(surface, cx, cy, radius - 3, light_color)

    # 边框
    aa_circle_outline(surface, cx, cy, radius, border_color)

def draw_hint_ring(
    surface: pygame.Surface,
    x: int,
    y: int,
    border_color: tuple[int, int, int],
    fill_color: tuple[int, int, int, int] | None = None,
    radius_padding: int = 6,
    border_width: int = 3,
    extra_outline_color: tuple[int, int, int] | None = None,
) -> None:
    rect = cell_rect(x, y)
    cx, cy = rect.center

    cell = ui.u(BOARD_CELL)
    radius = cell // 2 - ui.u(radius_padding)

    if fill_color is not None:
        overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(
            overlay,
            cell // 2,
            cell // 2,
            radius,
            fill_color,
        )
        pygame.gfxdraw.aacircle(
            overlay,
            cell // 2,
            cell // 2,
            radius,
            fill_color,
        )
        surface.blit(overlay, rect.topleft)

    for i in range(border_width):
        aa_circle_outline(surface, cx, cy, radius - i, border_color)

    if extra_outline_color is not None:
        aa_circle_outline(surface, cx, cy, radius + ui.u(2), extra_outline_color)

def draw_hover_cell_shadow(
    surface: pygame.Surface,
    hovered_cell: tuple[int, int] | None,
) -> None:
    if hovered_cell is None:
        return

    x, y = hovered_cell
    rect = cell_rect(x, y)

    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill(CELL_HOVER_FILL)
    surface.blit(overlay, rect.topleft)

def draw_arrow_hint_triangle(
    surface: pygame.Surface,
    points: list[tuple[int, int]],
) -> None:
    if len(points) != 3:
        return

    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)

    overlay = pygame.Surface((max_x - min_x + 1, max_y - min_y + 1), pygame.SRCALPHA)
    shifted = [(x - min_x, y - min_y) for x, y in points]

    pygame.gfxdraw.filled_polygon(overlay, shifted, ARROW_HINT_COLOR)
    pygame.gfxdraw.aapolygon(overlay, shifted, ARROW_HINT_COLOR)
    surface.blit(overlay, (min_x, min_y))

def draw_muzzle_arrow_hints(
    surface: pygame.Surface,
    cannon_infos: list[dict[str, Any]],
) -> None:
    for info in cannon_infos:
        if info.get("type") != "muzzle":
            continue

        cannon = info.get("cannon", {})
        positions = cannon.get("positions", [])
        if not positions:
            continue

        xs = [pos.get("x") for pos in positions if isinstance(pos.get("x"), int)]
        ys = [pos.get("y") for pos in positions if isinstance(pos.get("y"), int)]
        if not xs or not ys:
            continue

        direction = info.get("direction")
        cell = ui.u(BOARD_CELL)

        if direction == "left":
            target_x = min(xs)
            target_y = ys[0]
            rect = cell_rect(target_x, target_y)
            cx = rect.left + cell // 6
            cy = rect.centery
            points = [
                (cx - cell // 10, cy),
                (cx + cell // 10, cy - cell // 6),
                (cx + cell // 10, cy + cell // 6),
            ]

        elif direction == "right":
            target_x = max(xs)
            target_y = ys[0]
            rect = cell_rect(target_x, target_y)
            cx = rect.right - cell // 6
            cy = rect.centery
            points = [
                (cx + cell // 10, cy),
                (cx - cell // 10, cy - cell // 6),
                (cx - cell // 10, cy + cell // 6),
            ]

        elif direction == "up":
            target_x = xs[0]
            target_y = min(ys)
            rect = cell_rect(target_x, target_y)
            cx = rect.centerx
            cy = rect.top + cell // 6
            points = [
                (cx, cy - cell // 10),
                (cx - cell // 6, cy + cell // 10),
                (cx + cell // 6, cy + cell // 10),
            ]

        elif direction == "down":
            target_x = xs[0]
            target_y = max(ys)
            rect = cell_rect(target_x, target_y)
            cx = rect.centerx
            cy = rect.bottom - cell // 6
            points = [
                (cx, cy + cell // 10),
                (cx - cell // 6, cy - cell // 10),
                (cx + cell // 6, cy - cell // 10),
            ]
        else:
            continue

        draw_arrow_hint_triangle(surface, points)

def cell_rect(x: int, y: int) -> pygame.Rect:
    cell = ui.u(BOARD_CELL)
    px = ui.x(BOARD_ORIGIN_X) + (x - 1) * cell
    py = ui.y(BOARD_ORIGIN_Y) + (y - 1) * cell
    return pygame.Rect(px, py, cell, cell)

def cell_center(x: int, y: int) -> tuple[int, int]:
    rect = cell_rect(x, y)
    return rect.centerx, rect.centery

def draw_board_stars(surface: pygame.Surface) -> None:
    # 9x9 棋盘可先画 5 个点：中心 + 四角近中心
    star_points = [(3, 3), (3, 7), (5, 5), (7, 3), (7, 7)]

    for x, y in star_points:
        cx, cy = cell_center(x, y)
        aa_filled_circle(surface, cx, cy, 3, BOARD_STAR_COLOR)

def draw_capturable_targets(
    surface: pygame.Surface,
    capturable_cells: list[tuple[int, int]],
    hovered_cells: list[tuple[int, int]],
) -> None:
    hovered_set = set(hovered_cells)

    for x, y in capturable_cells:
        draw_hint_ring(
            surface,
            x,
            y,
            border_color=CAPTURABLE_COLOR,
            fill_color=CAPTURABLE_FILL,
            radius_padding=7,
            border_width=3,
            extra_outline_color=HOVER_CANNON_COLOR if (x, y) in hovered_set else None,
        )

def draw_cannon_highlights(
    surface: pygame.Surface,
    cannon_infos: list[dict[str, Any]],
    color: tuple[int, int, int],
    hovered_signatures: set[tuple] | None = None,
) -> None:
    if hovered_signatures is None:
        hovered_signatures = set()

    fill_color = CANNON_FILL if color == CANNON_HIGHLIGHT_COLOR else HOVER_CANNON_FILL

    for info in cannon_infos:
        cannon = info.get("cannon", {})
        positions = cannon.get("positions", [])
        signature = tuple((pos.get("x"), pos.get("y")) for pos in positions)

        centers: list[tuple[int, int]] = []
        for pos in positions:
            x = pos.get("x")
            y = pos.get("y")
            if isinstance(x, int) and isinstance(y, int):
                centers.append(cell_center(x, y))

                draw_hint_ring(
                    surface,
                    x,
                    y,
                    border_color=color,
                    fill_color=fill_color,
                    radius_padding=5,
                    border_width=3,
                    extra_outline_color=(
                        HOVER_CANNON_COLOR if signature in hovered_signatures else None
                    ),
                )

        if len(centers) >= 2:
            pygame.draw.lines(surface, color, False, centers, 4)
            pygame.draw.aalines(surface, color, False, centers)

            if signature in hovered_signatures:
                pygame.draw.lines(surface, HOVER_CANNON_COLOR, False, centers, 6)
                pygame.draw.aalines(surface, HOVER_CANNON_COLOR, False, centers)

def draw_board(
    surface: pygame.Surface,
    board_data: list[list[dict[str, Any] | None]],
    preview_board_data: list[list[dict[str, Any] | None]] | None,
    legal_highlights: dict[tuple[int, int], str],
    capturable_cells: list[tuple[int, int]],
    hovered_eat_cells: list[tuple[int, int]],
    cannon_highlights: list[dict[str, Any]],
    hovered_cannon_highlights: list[dict[str, Any]],
    hovered_cell: tuple[int, int] | None,
    fonts: dict[str, pygame.font.Font],
    arrow_hint_enabled: bool,
) -> None:
    cell = ui.u(BOARD_CELL)
    board_size_px = BOARD_SIZE * cell
    origin_x = ui.x(BOARD_ORIGIN_X)
    origin_y = ui.y(BOARD_ORIGIN_Y)

    board_rect = pygame.Rect(
        ui.x(BOARD_ORIGIN_X),
        ui.y(BOARD_ORIGIN_Y),
        board_size_px,
        board_size_px,
    )

    pygame.draw.rect(surface, BOARD_BG, board_rect, border_radius=6)
    pygame.draw.rect(surface, BOARD_LINE_DARK, board_rect, 3, border_radius=6)
    draw_hover_cell_shadow(surface, hovered_cell)

    # 高亮合法格
    for (x, y), mode in legal_highlights.items():
        if mode == "place":
            draw_hint_ring(
                surface,
                x,
                y,
                border_color=LEGAL_PLACE_COLOR,
                fill_color=LEGAL_PLACE_FILL,
                radius_padding=7,
                border_width=3,
            )
        else:
            draw_hint_ring(
                surface,
                x,
                y,
                border_color=LEGAL_UPGRADE_COLOR,
                fill_color=LEGAL_UPGRADE_FILL,
                radius_padding=7,
                border_width=3,
            )

    # 网格线
    for i in range(BOARD_SIZE + 1):
        px = origin_x + i * cell
        py = origin_y + i * cell

        pygame.draw.line(
            surface,
            BOARD_LINE_LIGHT,
            (px, origin_y),
            (px, origin_y + board_size_px),
            1,
        )
        pygame.draw.aaline(
            surface,
            BOARD_LINE_LIGHT,
            (px, origin_y),
            (px, origin_y + board_size_px),
        )

        pygame.draw.line(
            surface,
            BOARD_LINE_LIGHT,
            (origin_x, py),
            (origin_x + board_size_px, py),
            1,
        )
        pygame.draw.aaline(
            surface,
            BOARD_LINE_LIGHT,
            (origin_x, py),
            (origin_x + board_size_px, py),
        )
    draw_board_stars(surface)

    hovered_signatures = {
        tuple((pos.get("x"), pos.get("y")) for pos in info.get("cannon", {}).get("positions", []))
        for info in hovered_cannon_highlights
    }

    draw_cannon_highlights(
        surface,
        cannon_highlights,
        CANNON_HIGHLIGHT_COLOR,
        hovered_signatures=hovered_signatures,
    )

    if arrow_hint_enabled:
        draw_muzzle_arrow_hints(surface, cannon_highlights)

    draw_capturable_targets(
        surface,
        capturable_cells,
        hovered_eat_cells,
    )

    # 坐标标记
    for i in range(BOARD_SIZE):
        label = str(i + 1)
        draw_text(
            surface,
            label,
            fonts["small"],
            TEXT_COLOR,
            origin_x + i * cell + cell // 2 - ui.x(8),
            origin_y - ui.y(36),
        )
        draw_text(
            surface,
            label,
            fonts["small"],
            TEXT_COLOR,
            origin_x - ui.x(36),
            origin_y + i * cell + cell // 2 - ui.y(12),
        )

    # 棋子
    for y in range(1, BOARD_SIZE + 1):
        for x in range(1, BOARD_SIZE + 1):
            piece = board_data[y - 1][x - 1]
            if piece is None:
                continue

            color = piece.get("color")
            level = piece.get("level", "?")

            cx, cy = cell_center(x, y)
            radius = cell // 2 - ui.u(8)

            if color == "R":
                draw_piece_disc(
                    surface,
                    (cx, cy),
                    radius,
                    RED_PIECE_LIGHT,
                    RED_PIECE_DARK,
                    BOARD_LINE_DARK,
                )
            else:
                draw_piece_disc(
                    surface,
                    (cx, cy),
                    radius,
                    BLUE_PIECE_LIGHT,
                    BLUE_PIECE_DARK,
                    BOARD_LINE_DARK,
                )
            txt = fonts["piece"].render(str(level), True, (248, 248, 248))
            txt_rect = txt.get_rect(center=(cx, cy))
            surface.blit(txt, txt_rect)

    if preview_board_data is not None:
        preview_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)

        for y in range(1, BOARD_SIZE + 1):
            for x in range(1, BOARD_SIZE + 1):
                piece = preview_board_data[y - 1][x - 1]
                if piece is None:
                    continue

                color = piece.get("color")
                level = piece.get("level", "?")

                cx, cy = cell_center(x, y)
                radius = cell // 2 - ui.u(8)

                if color == "R":
                    draw_piece_disc(
                        preview_surface,
                        (cx, cy),
                        radius,
                        RED_PIECE_LIGHT,
                        RED_PIECE_DARK,
                        BOARD_LINE_DARK,
                    )
                else:
                    draw_piece_disc(
                        preview_surface,
                        (cx, cy),
                        radius,
                        BLUE_PIECE_LIGHT,
                        BLUE_PIECE_DARK,
                        BOARD_LINE_DARK,
                    )

                txt = fonts["piece"].render(str(level), True, (248, 248, 248))
                txt_rect = txt.get_rect(center=(cx, cy))
                preview_surface.blit(txt, txt_rect)

        preview_surface.set_alpha(110)
        surface.blit(preview_surface, (0, 0))

def draw_button(
    surface: pygame.Surface,
    text: str,
    rect: pygame.Rect,
    fonts: dict[str, pygame.font.Font],
    hovered: bool = False,
) -> None:
    bg = BUTTON_HOVER_BG if hovered else BUTTON_BG
    border = BUTTON_HOVER_BORDER if hovered else BUTTON_BORDER

    pygame.draw.rect(surface, bg, rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, 2, border_radius=10)

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
    shadow = rect.move(ui.x(6), ui.y(6))
    shadow_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
    shadow_surf.fill(MODAL_SHADOW)
    surface.blit(shadow_surf, shadow.topleft)

    pygame.draw.rect(surface, bg_color, rect, border_radius=ui.u(14))
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=ui.u(14))

def draw_action_buttons(
    surface: pygame.Surface,
    actions: list[dict[str, Any]],
    fonts: dict[str, pygame.font.Font],
    start_x: int,
    start_y: int,
    width: int,
    mouse_pos: tuple[int, int] | None,
) -> tuple[list[tuple[pygame.Rect, dict[str, Any]]], int]:
    button_items: list[tuple[pygame.Rect, dict[str, Any]]] = []

    shown_actions = actions[:ACTION_BUTTON_MAX_COUNT]
    y = start_y

    for action in shown_actions:
        rect = pygame.Rect(
            start_x,
            y,
            ui.x(ACTION_BUTTON_WIDTH),
            ui.y(ACTION_BUTTON_HEIGHT),
        )

        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        draw_button(surface, action.get("label", str(action)), rect, fonts, hovered=hovered)

        button_items.append((rect, action))
        y += ui.y(ACTION_BUTTON_HEIGHT + ACTION_BUTTON_GAP)

    return button_items, y

def draw_system_buttons(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    start_x: int,
    start_y: int,
    mouse_pos: tuple[int, int] | None,
) -> tuple[dict[str, pygame.Rect], int]:
    buttons: dict[str, pygame.Rect] = {}

    labels = ["undo", "backtrack", "restart", "settings"]
    texts = {
        "undo": "撤销",
        "backtrack": "回退",
        "restart": "重开",
        "settings": "设置",
    }

    for i, key in enumerate(labels):
        col = i

        rect = pygame.Rect(
            start_x + col * ui.x(SYSTEM_BUTTON_WIDTH + SYSTEM_BUTTON_GAP),
            start_y,
            ui.x(SYSTEM_BUTTON_WIDTH),
            ui.y(SYSTEM_BUTTON_HEIGHT),
        )

        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        draw_button(surface, texts[key], rect, fonts, hovered=hovered)
        buttons[key] = rect

    end_y = start_y + ui.y(SYSTEM_BUTTON_HEIGHT + SYSTEM_BUTTON_GAP)
    return buttons, end_y

def draw_extra_buttons(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    start_x: int,
    start_y: int,
    mouse_pos: tuple[int, int] | None,
    record_open: bool,
) -> dict[str, pygame.Rect]:
    result: dict[str, pygame.Rect] = {}

    record_rect = pygame.Rect(
        start_x,
        start_y,
        ui.x(TOGGLE_RECORD_BUTTON_WIDTH),
        ui.y(TOGGLE_RECORD_BUTTON_HEIGHT),
    )
    draw_button(
        surface,
        "关闭棋谱" if record_open else "打开棋谱",
        record_rect,
        fonts,
        hovered=(mouse_pos is not None and record_rect.collidepoint(mouse_pos)),
    )
    result["toggle_record"] = record_rect

    endgame_rect = pygame.Rect(
        start_x,
        start_y + ui.y(TOGGLE_RECORD_BUTTON_HEIGHT + 18),
        ui.x(ENDGAME_BUTTON_WIDTH),
        ui.y(ENDGAME_BUTTON_HEIGHT),
    )
    draw_danger_button(
        surface,
        "终局",
        endgame_rect,
        fonts,
        hovered=(mouse_pos is not None and endgame_rect.collidepoint(mouse_pos)),
    )
    result["endgame"] = endgame_rect

    resign_rect = pygame.Rect(
        start_x + ui.x(ENDGAME_BUTTON_WIDTH + 18),
        start_y + ui.y(TOGGLE_RECORD_BUTTON_HEIGHT + 18),
        ui.x(RESIGN_BUTTON_WIDTH),
        ui.y(RESIGN_BUTTON_HEIGHT),
    )
    draw_danger_button(
        surface,
        "投降",
        resign_rect,
        fonts,
        hovered=(mouse_pos is not None and resign_rect.collidepoint(mouse_pos)),
    )
    result["resign"] = resign_rect

    return result

def draw_record_panel(
    surface: pygame.Surface,
    history: list[str],
    record_scroll: int,
    fonts: dict[str, pygame.font.Font],
) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}

    panel_rect = pygame.Rect(
        ui.x(500),
        ui.y(180),
        ui.x(RECORD_PANEL_WIDTH),
        ui.y(RECORD_PANEL_HEIGHT),
    )
    rects["record_panel"] = panel_rect

    draw_card_panel(surface, panel_rect, RECORD_PANEL_BG, RECORD_PANEL_BORDER)

    title_x = panel_rect.x + ui.x(24)
    title_y = panel_rect.y + ui.y(20)
    draw_text(surface, "全部棋谱", fonts["heading"], TEXT_COLOR, title_x, title_y)

    up_rect = pygame.Rect(
        panel_rect.right - ui.x(260),
        panel_rect.y + ui.y(18),
        ui.x(64),
        ui.y(40),
    )
    down_rect = pygame.Rect(
        panel_rect.right - ui.x(84),
        panel_rect.y + ui.y(18),
        ui.x(64),
        ui.y(40),
    )
    draw_button(surface, "上翻", up_rect, fonts, hovered=False)
    draw_button(surface, "下翻", down_rect, fonts, hovered=False)

    rects["record_up"] = up_rect
    rects["record_down"] = down_rect

    total_pages = max(1, (len(history) + RECORD_LINE_COUNT - 1) // RECORD_LINE_COUNT)
    current_page = max(1, record_scroll + 1)

    page_text = f"第 {current_page} / {total_pages} 页"
    page_img = fonts["small"].render(page_text, True, TEXT_COLOR)
    page_rect = page_img.get_rect(center=(panel_rect.right - ui.x(145), panel_rect.y + ui.y(38)))
    surface.blit(page_img, page_rect)

    start = max(0, min(record_scroll * RECORD_LINE_COUNT, max(0, len(history) - RECORD_LINE_COUNT)))
    visible = history[start:start + RECORD_LINE_COUNT]

    y = panel_rect.y + ui.y(90)
    for i, line in enumerate(visible, start=1):
        draw_text(
            surface,
            line,
            fonts["small"],
            TEXT_COLOR,
            panel_rect.x + ui.x(24),
            y,
        )
        y += font_h(fonts["small"]) + ui.y(14)

    return rects

def draw_confirm_modal(
    surface: pygame.Surface,
    title: str,
    message: str,
    fonts: dict[str, pygame.font.Font],
) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}

    panel_rect = pygame.Rect(
        (LOGICAL_WIDTH - ui.x(MODAL_WIDTH)) // 2,
        (LOGICAL_HEIGHT - ui.y(MODAL_HEIGHT)) // 2,
        ui.x(MODAL_WIDTH),
        ui.y(MODAL_HEIGHT),
    )
    rects["confirm_panel"] = panel_rect

    draw_card_panel(surface, panel_rect, MODAL_BG, MODAL_BORDER)

    draw_text(surface, title, fonts["heading"], TEXT_COLOR, panel_rect.x + ui.x(28), panel_rect.y + ui.y(26))
    draw_multiline_text(
        surface,
        message,
        fonts["body"],
        TEXT_COLOR,
        panel_rect.x + ui.x(28),
        panel_rect.y + ui.y(90),
        line_gap=ui.y(8),
        max_lines=3,
    )

    cancel_rect = pygame.Rect(
        panel_rect.x + ui.x(120),
        panel_rect.bottom - ui.y(90),
        ui.x(180),
        ui.y(56),
    )
    confirm_rect = pygame.Rect(
        panel_rect.right - ui.x(300),
        panel_rect.bottom - ui.y(90),
        ui.x(180),
        ui.y(56),
    )

    draw_button(surface, "取消", cancel_rect, fonts, hovered=False)
    draw_danger_button(surface, "确定", confirm_rect, fonts, hovered=False)

    rects["cancel"] = cancel_rect
    rects["confirm"] = confirm_rect
    return rects

def draw_settings_panel(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
    record_open: bool,
    arrow_hint_enabled: bool,
    preview_drop_enabled: bool,
    preview_eat_enabled: bool,
    preview_fire_enabled: bool,
) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}

    panel_rect = pygame.Rect(
        (LOGICAL_WIDTH - ui.x(SETTINGS_PANEL_WIDTH)) // 2,
        (LOGICAL_HEIGHT - ui.y(SETTINGS_PANEL_HEIGHT)) // 2,
        ui.x(SETTINGS_PANEL_WIDTH),
        ui.y(SETTINGS_PANEL_HEIGHT),
    )
    rects["settings_panel"] = panel_rect
    draw_card_panel(surface, panel_rect, MODAL_BG, MODAL_BORDER)

    draw_text(surface, "设置", fonts["heading"], TEXT_COLOR, panel_rect.x + ui.x(32), panel_rect.y + ui.y(18))

    labels = [
        ("open_save_slots", "保存到存档槽"),
        ("open_load_slots", "从存档槽载入"),
        ("toggle_record", "关闭棋谱" if record_open else "打开棋谱"),
        ("toggle_arrow_hint", f"端点提示：{'开' if arrow_hint_enabled else '关'}"),
        ("toggle_preview_drop", f"落子预览：{'开' if preview_drop_enabled else '关'}"),
        ("toggle_preview_eat", f"吃子预览：{'开' if preview_eat_enabled else '关'}"),
        ("toggle_preview_fire", f"打炮预览：{'开' if preview_fire_enabled else '关'}"),
        ("export_record", "导出棋谱"),
        ("endgame", "终局"),
        ("resign", "投降"),
        ("close_settings", "关闭设置"),
        ("quit_game", "退出游戏"),
    ]

    start_y = panel_rect.y + ui.y(88)
    for i, (key, text) in enumerate(labels):
        row = i // 2
        col = i % 2

        rect = pygame.Rect(
            panel_rect.x + ui.x(42) + col * ui.x(360),
            start_y + row * ui.y(60),
            ui.x(320),
            ui.y(46),
        )

        if key in {"quit_game", "endgame", "resign"}:
            draw_danger_button(
                surface,
                text,
                rect,
                fonts,
                hovered=(mouse_pos is not None and rect.collidepoint(mouse_pos)),
            )
        else:
            draw_button(
                surface,
                text,
                rect,
                fonts,
                hovered=(mouse_pos is not None and rect.collidepoint(mouse_pos)),
            )

        rects[key] = rect

    return rects

def draw_slot_panel(
    surface: pygame.Surface,
    title: str,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
    prefix: str,
) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}

    panel_rect = pygame.Rect(
        (LOGICAL_WIDTH - ui.x(560)) // 2,
        (LOGICAL_HEIGHT - ui.y(300)) // 2,
        ui.x(560),
        ui.y(300),
    )
    rects[f"{prefix}_panel"] = panel_rect
    draw_card_panel(surface, panel_rect, MODAL_BG, MODAL_BORDER)

    draw_text(surface, title, fonts["heading"], TEXT_COLOR, panel_rect.x + ui.x(28), panel_rect.y + ui.y(24))

    labels = [
        (f"{prefix}_1", "槽位 1"),
        (f"{prefix}_2", "槽位 2"),
        (f"{prefix}_3", "槽位 3"),
        (f"{prefix}_cancel", "取消"),
    ]

    for i, (key, text) in enumerate(labels):
        rect = pygame.Rect(
            panel_rect.x + ui.x(40),
            panel_rect.y + ui.y(80) + i * ui.y(54),
            ui.x(220),
            ui.y(42),
        )
        draw_button(
            surface,
            text,
            rect,
            fonts,
            hovered=(mouse_pos is not None and rect.collidepoint(mouse_pos)),
        )
        rects[key] = rect

    return rects

def draw_main_menu(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
    load_open: bool,
) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}

    surface.fill(BG_COLOR)

    panel_rect = pygame.Rect(
        (LOGICAL_WIDTH - ui.x(600)) // 2,
        (LOGICAL_HEIGHT - ui.y(420)) // 2,
        ui.x(600),
        ui.y(420),
    )
    rects["menu_panel"] = panel_rect
    draw_card_panel(surface, panel_rect, MODAL_BG, MODAL_BORDER)

    title_font = ui.font("microsoftyaheiui", 64, bold=True)
    subtitle_font = ui.font("microsoftyaheiui", 30, bold=True)

    title_img = title_font.render("炮棋", True, TEXT_COLOR)
    title_rect = title_img.get_rect(center=(panel_rect.centerx, panel_rect.y + ui.y(72)))
    surface.blit(title_img, title_rect)

    subtitle_img = subtitle_font.render("桌面版", True, TEXT_COLOR)
    subtitle_rect = subtitle_img.get_rect(center=(panel_rect.centerx, panel_rect.y + ui.y(142)))
    surface.blit(subtitle_img, subtitle_rect)

    start_rect = pygame.Rect(panel_rect.x + ui.x(170), panel_rect.y + ui.y(180), ui.x(260), ui.y(56))
    load_rect = pygame.Rect(panel_rect.x + ui.x(170), panel_rect.y + ui.y(255), ui.x(260), ui.y(56))
    quit_rect = pygame.Rect(panel_rect.x + ui.x(170), panel_rect.y + ui.y(330), ui.x(260), ui.y(56))

    draw_button(surface, "开始游戏", start_rect, fonts, hovered=(mouse_pos is not None and start_rect.collidepoint(mouse_pos)))
    draw_button(surface, "载入存档", load_rect, fonts, hovered=(mouse_pos is not None and load_rect.collidepoint(mouse_pos)))
    draw_danger_button(surface, "退出", quit_rect, fonts, hovered=(mouse_pos is not None and quit_rect.collidepoint(mouse_pos)))

    rects["menu_start"] = start_rect
    rects["menu_load"] = load_rect
    rects["menu_quit"] = quit_rect

    if load_open:
        rects.update(
            draw_slot_panel(
                surface,
                "选择存档槽位",
                fonts,
                mouse_pos,
                "menu_load_slot",
            )
        )

    return rects

def draw_phase_badge(
    surface: pygame.Surface,
    phase: str,
    phase_name: str,
    x: int,
    y: int,
    fonts: dict[str, pygame.font.Font],
) -> None:
    color_map = {
        "drop": PHASE_DROP_COLOR,
        "muzzle": PHASE_MUZZLE_COLOR,
        "fire": PHASE_FIRE_COLOR,
        "eat": PHASE_EAT_COLOR,
    }
    color = color_map.get(phase, BUTTON_BORDER)

    rect = pygame.Rect(x, y, ui.x(240), ui.y(42))
    pygame.draw.rect(surface, color, rect, border_radius=8)

    txt = fonts["small"].render(phase_name, True, (255, 255, 255))
    txt_rect = txt.get_rect(center=rect.center)
    surface.blit(txt, txt_rect)

def draw_game_over_overlay(
    surface: pygame.Surface,
    snapshot: dict[str, Any],
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}
    phase_info = snapshot.get("phase_info", {})
    if not phase_info.get("game_over", False):
        return rects

    overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_BG)
    surface.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(LOGICAL_WIDTH // 2 - 300, LOGICAL_HEIGHT // 2 - 140, 600, 280)
    rects["game_over_panel"] = panel_rect
    draw_card_panel(surface, panel_rect, OVERLAY_PANEL_BG, OVERLAY_PANEL_BORDER)

    winner = phase_info.get("winner")
    if winner == "R":
        title = "游戏结束：红方获胜"
        color = RED_PIECE
    elif winner == "B":
        title = "游戏结束：蓝方获胜"
        color = BLUE_PIECE
    else:
        title = "游戏结束"
        color = TEXT_COLOR

    big_title_font = ui.font("microsoftyaheiui", 42, bold=True)
    big_body_font = ui.font("microsoftyaheiui", 28)

    draw_text(surface, title, big_title_font, color, panel_rect.x + 56, panel_rect.y + 42)
    draw_text(surface, "请选择下方操作：", big_body_font, TEXT_COLOR, panel_rect.x + 56, panel_rect.y + 118)

    restart_rect = pygame.Rect(panel_rect.x + 28, panel_rect.y + 178, ui.x(130), ui.y(54))
    load_rect = pygame.Rect(panel_rect.x + 170, panel_rect.y + 178, ui.x(130), ui.y(54))
    export_rect = pygame.Rect(panel_rect.x + 312, panel_rect.y + 178, ui.x(130), ui.y(54))
    quit_rect = pygame.Rect(panel_rect.x + 454, panel_rect.y + 178, ui.x(130), ui.y(54))

    draw_button(surface, "重开", restart_rect, fonts, hovered=(mouse_pos is not None and restart_rect.collidepoint(mouse_pos)))
    draw_button(surface, "载入", load_rect, fonts, hovered=(mouse_pos is not None and load_rect.collidepoint(mouse_pos)))
    draw_button(surface, "导出棋谱", export_rect, fonts, hovered=(mouse_pos is not None and export_rect.collidepoint(mouse_pos)))
    draw_danger_button(surface, "退出游戏", quit_rect, fonts, hovered=(mouse_pos is not None and quit_rect.collidepoint(mouse_pos)))

    rects["game_over_restart"] = restart_rect
    rects["game_over_load"] = load_rect
    rects["game_over_export"] = export_rect
    rects["game_over_quit"] = quit_rect

    return rects

def draw_panel(
    surface: pygame.Surface,
    snapshot: dict[str, Any],
    status_message: str,
    status_is_error: bool,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
    record_open: bool,
) -> tuple[list[tuple[pygame.Rect, dict[str, Any]]], dict[str, pygame.Rect]]:
    panel_rect = ui.rect(SIDEBAR_X, SIDEBAR_Y, SIDEBAR_WIDTH, SIDEBAR_HEIGHT)
    shadow_rect = panel_rect.move(ui.x(4), ui.y(4))
    pygame.draw.rect(surface, PANEL_SHADOW, shadow_rect, border_radius=ui.u(12))
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=ui.u(12))
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, 2, border_radius=ui.u(12))

    phase_info = snapshot.get("phase_info", {})
    logs = snapshot.get("logs", {})
    legal_info = snapshot.get("legal_actions", {})

    pad_x = ui.x(20)
    pad_y = ui.y(18)

    left_x = panel_rect.x + pad_x
    right_col_x = panel_rect.x + ui.x(560)
    top_y = panel_rect.y + pad_y
    bottom_y = panel_rect.bottom - pad_y

    section_gap = ui.y(20)
    line_gap_small = ui.y(4)
    label_gap = ui.y(8)

    # ===== 标题行 =====
    title_y = top_y
    draw_text(surface, "炮棋 Pygame UI", fonts["title"], TEXT_COLOR, left_x, title_y)

    phase_badge_w = ui.x(240)
    phase_badge_x = panel_rect.right - pad_x - phase_badge_w
    draw_phase_badge(
        surface,
        phase_info.get("phase", ""),
        phase_info.get("phase_name", ""),
        phase_badge_x,
        title_y + ui.y(2),
        fonts,
    )

    y = title_y + font_h(fonts["title"]) + section_gap

    # ===== 基本状态 =====
    current_player = phase_info.get("current_player", "")
    current_player_name = phase_info.get("current_player_name", current_player)
    player_color = RED_PIECE if current_player == "R" else BLUE_PIECE

    draw_text(surface, "当前玩家：", fonts["body"], TEXT_COLOR, left_x, y)
    draw_text(surface, current_player_name, fonts["body"], player_color, left_x + ui.x(150), y)
    y += font_h(fonts["body"]) + label_gap

    draw_text(
        surface,
        f"当前阶段：{phase_info.get('phase_name', phase_info.get('phase', ''))}",
        fonts["body"],
        TEXT_COLOR,
        left_x,
        y,
    )
    y += font_h(fonts["body"]) + label_gap

    draw_text(
        surface,
        f"回合数：{phase_info.get('turn_number', '')}",
        fonts["body"],
        TEXT_COLOR,
        left_x,
        y,
    )
    y += font_h(fonts["body"]) + label_gap

    # ===== 最近动作 =====
    history = logs.get("history", [])
    last_record = history[-1] if history else "（暂无）"

    draw_text(surface, "最近动作", fonts["heading"], TEXT_COLOR, left_x, y)
    y += font_h(fonts["heading"]) + ui.y(6)

    draw_multiline_text(
        surface,
        last_record,
        fonts["small"],
        TEXT_COLOR,
        left_x,
        y,
        line_gap=line_gap_small,
        max_lines=2,
    )
    y += multiline_block_height(last_record, fonts["small"], line_gap_small, max_lines=2) + section_gap

    # ===== 提示 =====
    draw_text(surface, "提示", fonts["heading"], TEXT_COLOR, left_x, y)
    y += font_h(fonts["heading"]) + ui.y(6)

    status_color = STATUS_ERR if status_is_error else STATUS_OK
    draw_multiline_text(
        surface,
        status_message or "请选择一个合法动作。",
        fonts["small"],
        status_color,
        left_x,
        y,
        line_gap=line_gap_small,
        max_lines=3,
    )
    y += multiline_block_height(
        status_message or "请选择一个合法动作。",
        fonts["small"],
        line_gap_small,
        max_lines=3,
    ) + section_gap

    # ===== 动作按钮区 =====
    draw_text(surface, "系统操作", fonts["heading"], TEXT_COLOR, left_x, y)
    y += font_h(fonts["heading"]) + ui.y(8)

    system_button_rects, system_end_y = draw_system_buttons(
        surface,
        fonts,
        start_x=left_x,
        start_y=y,
        mouse_pos=mouse_pos,
    )

    action_button_items: list[tuple[pygame.Rect, dict[str, Any]]] = []
    content_end_y = system_end_y + section_gap

    # ===== 退出按钮固定底部 =====
    quit_rect = ui.rect(
        SIDEBAR_X + 730,
        SIDEBAR_Y + 868,
        QUIT_BUTTON_WIDTH,
        QUIT_BUTTON_HEIGHT,
    )
    quit_hovered = mouse_pos is not None and quit_rect.collidepoint(mouse_pos)
    draw_button(surface, "退出程序", quit_rect, fonts, hovered=quit_hovered)

    return action_button_items, system_button_rects

def render_all(
    surface: pygame.Surface,
    snapshot: dict[str, Any],
    preview_board_data: list[list[dict[str, Any] | None]] | None,
    legal_highlights: dict[tuple[int, int], str],
    capturable_cells: list[tuple[int, int]],
    hovered_eat_cells: list[tuple[int, int]],
    cannon_highlights: list[dict[str, Any]],
    hovered_cannon_highlights: list[dict[str, Any]],
    hovered_cell: tuple[int, int] | None,
    status_message: str,
    status_is_error: bool,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
    record_open: bool,
    history: list[str],
    record_scroll: int,
    confirm_dialog: dict[str, str] | None,
    settings_open: bool,
    arrow_hint_enabled: bool,
    preview_drop_enabled: bool,
    preview_eat_enabled: bool,
    preview_fire_enabled: bool,
    app_mode: str,
    menu_load_open: bool,
    settings_save_open: bool,
    settings_load_open: bool,
) -> tuple[list[tuple[pygame.Rect, dict[str, Any]]], dict[str, pygame.Rect], dict[str, pygame.Rect]]:
    overlay_buttons: dict[str, pygame.Rect] = {}

    if app_mode == "menu":
        surface.fill(BG_COLOR)
        overlay_buttons.update(
            draw_main_menu(
                surface,
                fonts,
                mouse_pos,
                menu_load_open,
            )
        )
        return [], {}, overlay_buttons

    surface.fill(BG_COLOR)

    board_data = snapshot.get("board", [])

    draw_board(
        surface,
        board_data,
        preview_board_data,
        legal_highlights,
        capturable_cells,
        hovered_eat_cells,
        cannon_highlights,
        hovered_cannon_highlights,
        hovered_cell,
        fonts,
        arrow_hint_enabled,
    )

    button_items, system_buttons = draw_panel(
        surface,
        snapshot,
        status_message,
        status_is_error,
        fonts,
        mouse_pos,
        record_open,
    )

    game_over_buttons = draw_game_over_overlay(
        surface,
        snapshot,
        fonts,
        mouse_pos,
    )
    if game_over_buttons:
        overlay_buttons.update(game_over_buttons)
        return button_items, system_buttons, overlay_buttons

    if record_open and not settings_open and confirm_dialog is None:
        overlay_buttons.update(
            draw_record_panel(
                surface,
                history,
                record_scroll,
                fonts,
            )
        )

    if settings_open:
        overlay_buttons.update(
            draw_settings_panel(
                surface,
                fonts,
                mouse_pos,
                record_open,
                arrow_hint_enabled,
                preview_drop_enabled,
                preview_eat_enabled,
                preview_fire_enabled,
            )
        )

        if settings_save_open:
            overlay_buttons.update(
                draw_slot_panel(
                    surface,
                    "选择保存槽位",
                    fonts,
                    mouse_pos,
                    "save_slot",
                )
            )

        if settings_load_open:
            overlay_buttons.update(
                draw_slot_panel(
                    surface,
                    "选择读取槽位",
                    fonts,
                    mouse_pos,
                    "load_slot",
                )
            )

    if confirm_dialog is not None:
        overlay_buttons.update(
            draw_confirm_modal(
                surface,
                confirm_dialog["title"],
                confirm_dialog["message"],
                fonts,
            )
        )

    return button_items, system_buttons, overlay_buttons

def get_quit_button_rect() -> pygame.Rect:
    return ui.rect(
        SIDEBAR_X + 730,
        SIDEBAR_Y + 868,
        QUIT_BUTTON_WIDTH,
        QUIT_BUTTON_HEIGHT,
    )

def get_action_button_rects_placeholder() -> list[tuple[pygame.Rect, dict[str, Any]]]:
    return []