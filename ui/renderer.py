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
    legal_highlights: dict[tuple[int, int], str],
    capturable_cells: list[tuple[int, int]],
    hovered_eat_cells: list[tuple[int, int]],
    cannon_highlights: list[dict[str, Any]],
    hovered_cannon_highlights: list[dict[str, Any]],
    hovered_cell: tuple[int, int] | None,
    fonts: dict[str, pygame.font.Font],
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

    labels = ["undo", "restart", "save", "load"]
    texts = {
        "undo": "Undo",
        "restart": "Restart",
        "save": "Save",
        "load": "Load",
    }

    for i, key in enumerate(labels):
        row = i // 2
        col = i % 2

        rect = pygame.Rect(
            start_x + col * ui.x(SYSTEM_BUTTON_WIDTH + SYSTEM_BUTTON_GAP),
            start_y + row * ui.y(SYSTEM_BUTTON_HEIGHT + SYSTEM_BUTTON_GAP),
            ui.x(SYSTEM_BUTTON_WIDTH),
            ui.y(SYSTEM_BUTTON_HEIGHT),
        )

        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        draw_button(surface, texts[key], rect, fonts, hovered=hovered)
        buttons[key] = rect

    end_y = start_y + 2 * (SYSTEM_BUTTON_HEIGHT + SYSTEM_BUTTON_GAP)
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

    shadow = panel_rect.move(ui.x(6), ui.y(6))
    shadow_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
    shadow_surf.fill(MODAL_SHADOW)
    surface.blit(shadow_surf, shadow.topleft)

    pygame.draw.rect(surface, RECORD_PANEL_BG, panel_rect, border_radius=ui.u(14))
    pygame.draw.rect(surface, RECORD_PANEL_BORDER, panel_rect, 2, border_radius=ui.u(14))

    title_x = panel_rect.x + ui.x(24)
    title_y = panel_rect.y + ui.y(20)
    draw_text(surface, "全部棋谱", fonts["heading"], TEXT_COLOR, title_x, title_y)

    up_rect = pygame.Rect(
        panel_rect.right - ui.x(180),
        panel_rect.y + ui.y(18),
        ui.x(70),
        ui.y(42),
    )
    down_rect = pygame.Rect(
        panel_rect.right - ui.x(95),
        panel_rect.y + ui.y(18),
        ui.x(70),
        ui.y(42),
    )
    draw_button(surface, "上翻", up_rect, fonts, hovered=False)
    draw_button(surface, "下翻", down_rect, fonts, hovered=False)

    rects["record_up"] = up_rect
    rects["record_down"] = down_rect

    start = max(0, min(record_scroll, max(0, len(history) - RECORD_LINE_COUNT)))
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

    shadow = panel_rect.move(ui.x(6), ui.y(6))
    shadow_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
    shadow_surf.fill(MODAL_SHADOW)
    surface.blit(shadow_surf, shadow.topleft)

    pygame.draw.rect(surface, MODAL_BG, panel_rect, border_radius=ui.u(14))
    pygame.draw.rect(surface, MODAL_BORDER, panel_rect, 2, border_radius=ui.u(14))

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
    pygame.draw.rect(surface, OVERLAY_PANEL_BG, panel_rect, border_radius=14)
    pygame.draw.rect(surface, OVERLAY_PANEL_BORDER, panel_rect, 2, border_radius=14)

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

    restart_rect = pygame.Rect(panel_rect.x + 56, panel_rect.y + 178, ui.x(160), ui.y(54))
    load_rect = pygame.Rect(panel_rect.x + 240, panel_rect.y + 178, ui.x(160), ui.y(54))
    quit_rect = pygame.Rect(panel_rect.x + 424, panel_rect.y + 178, ui.x(160), ui.y(54))

    draw_button(surface, "Restart", restart_rect, fonts, hovered=(mouse_pos is not None and restart_rect.collidepoint(mouse_pos)))
    draw_button(surface, "Load", load_rect, fonts, hovered=(mouse_pos is not None and load_rect.collidepoint(mouse_pos)))
    draw_danger_button(surface, "退出游戏", quit_rect, fonts, hovered=(mouse_pos is not None and quit_rect.collidepoint(mouse_pos)))

    rects["game_over_restart"] = restart_rect
    rects["game_over_load"] = load_rect
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

    extra_button_rects = draw_extra_buttons(
        surface,
        fonts,
        start_x=left_x + ui.x(420),
        start_y=y,
        mouse_pos=mouse_pos,
        record_open=record_open,
    )
    system_button_rects.update(extra_button_rects)

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
) -> tuple[list[tuple[pygame.Rect, dict[str, Any]]], dict[str, pygame.Rect], dict[str, pygame.Rect]]:
    surface.fill(BG_COLOR)

    board_data = snapshot.get("board", [])

    draw_board(
        surface,
        board_data,
        legal_highlights,
        capturable_cells,
        hovered_eat_cells,
        cannon_highlights,
        hovered_cannon_highlights,
        hovered_cell,
        fonts,
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

    overlay_buttons: dict[str, pygame.Rect] = {}

    if record_open:
        overlay_buttons.update(draw_record_panel(surface, history, record_scroll, fonts))

    if confirm_dialog is not None:
        overlay_buttons.update(
            draw_confirm_modal(
                surface,
                confirm_dialog["title"],
                confirm_dialog["message"],
                fonts,
            )
        )

    overlay_buttons.update(draw_game_over_overlay(surface, snapshot, fonts, mouse_pos))
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