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
) -> None:
    for x, y in capturable_cells:
        draw_hint_ring(
            surface,
            x,
            y,
            border_color=CAPTURABLE_COLOR,
            fill_color=CAPTURABLE_FILL,
            radius_padding=7,
            border_width=3,
        )

def draw_cannon_highlights(
    surface: pygame.Surface,
    cannon_infos: list[dict[str, Any]],
    color: tuple[int, int, int],
) -> None:
    fill_color = CANNON_FILL if color == CANNON_HIGHLIGHT_COLOR else HOVER_CANNON_FILL

    for info in cannon_infos:
        cannon = info.get("cannon", {})
        positions = cannon.get("positions", [])

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
                )

        if len(centers) >= 2:
            pygame.draw.lines(surface, color, False, centers, 4)
            pygame.draw.aalines(surface, color, False, centers)

def draw_board(
    surface: pygame.Surface,
    board_data: list[list[dict[str, Any] | None]],
    legal_highlights: dict[tuple[int, int], str],
    capturable_cells: list[tuple[int, int]],
    cannon_highlights: list[dict[str, Any]],
    hover_cannon_highlights: list[dict[str, Any]],
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

    # 可发射炮 / 待选炮口高亮
    draw_cannon_highlights(surface, cannon_highlights, CANNON_HIGHLIGHT_COLOR)

    # 鼠标悬停的炮管高亮（优先更显眼）
    draw_cannon_highlights(surface, hover_cannon_highlights, HOVER_CANNON_COLOR)

    # 可吃目标高亮
    draw_capturable_targets(surface, capturable_cells)

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
) -> None:
    phase_info = snapshot.get("phase_info", {})
    if not phase_info.get("game_over", False):
        return

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

    draw_text(surface, title, fonts["heading"], color, panel_rect.x + 56, panel_rect.y + 48)
    draw_text(surface, "可点击 Restart / Load / Quit", fonts["body"], TEXT_COLOR, panel_rect.x + 56, panel_rect.y + 124)

def draw_panel(
    surface: pygame.Surface,
    snapshot: dict[str, Any],
    status_message: str,
    status_is_error: bool,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
) -> tuple[list[tuple[pygame.Rect, dict[str, Any]]], dict[str, pygame.Rect]]:
    panel_rect = ui.rect(SIDEBAR_X, SIDEBAR_Y, SIDEBAR_WIDTH, SIDEBAR_HEIGHT)
    shadow_rect = panel_rect.move(ui.x(4), ui.y(4))
    pygame.draw.rect(surface, PANEL_SHADOW, shadow_rect, border_radius=ui.u(12))
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=ui.u(12))
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, 2, border_radius=ui.u(12))

    phase_info = snapshot.get("phase_info", {})
    logs = snapshot.get("logs", {})
    legal_info = snapshot.get("legal_actions", {})
    actions = legal_info.get("actions", [])

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

    draw_text(
        surface,
        f"合法动作：{legal_info.get('count', 0)}",
        fonts["body"],
        TEXT_COLOR,
        left_x,
        y,
    )
    y += font_h(fonts["body"]) + section_gap

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
    draw_text(surface, "当前可执行动作", fonts["heading"], TEXT_COLOR, left_x, y)
    draw_text(surface, "系统操作", fonts["heading"], TEXT_COLOR, right_col_x, y)
    y += font_h(fonts["heading"]) + ui.y(8)

    action_button_items, action_end_y = draw_action_buttons(
        surface,
        actions,
        fonts,
        start_x=left_x,
        start_y=y,
        width=ACTION_BUTTON_WIDTH,
        mouse_pos=mouse_pos,
    )

    system_button_rects, system_end_y = draw_system_buttons(
        surface,
        fonts,
        start_x=right_col_x,
        start_y=y,
        mouse_pos=mouse_pos,
    )

    content_end_y = max(action_end_y, system_end_y) + section_gap

    # ===== 最近棋谱 =====
    history_y = content_end_y
    draw_text(surface, "最近棋谱", fonts["heading"], TEXT_COLOR, left_x, history_y)
    history_y += font_h(fonts["heading"]) + ui.y(6)

    history_text = "\n".join(history[-4:]) if history else "（暂无）"
    draw_multiline_text(
        surface,
        history_text,
        fonts["small"],
        TEXT_COLOR,
        left_x,
        history_y,
        line_gap=line_gap_small,
        max_lines=4,
    )

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
    cannon_highlights: list[dict[str, Any]],
    hover_cannon_highlights: list[dict[str, Any]],
    status_message: str,
    status_is_error: bool,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
) -> tuple[list[tuple[pygame.Rect, dict[str, Any]]], dict[str, pygame.Rect]]:
    surface.fill(BG_COLOR)

    board_data = snapshot.get("board", [])

    draw_board(
        surface,
        board_data,
        legal_highlights,
        capturable_cells,
        cannon_highlights,
        hover_cannon_highlights,
        fonts,
    )
    button_items, system_buttons = draw_panel(
        surface,
        snapshot,
        status_message,
        status_is_error,
        fonts,
        mouse_pos,
    )

    draw_game_over_overlay(surface, snapshot, fonts)
    return button_items, system_buttons

def get_quit_button_rect() -> pygame.Rect:
    return ui.rect(
        SIDEBAR_X + 730,
        SIDEBAR_Y + 868,
        QUIT_BUTTON_WIDTH,
        QUIT_BUTTON_HEIGHT,
    )

def get_action_button_rects_placeholder() -> list[tuple[pygame.Rect, dict[str, Any]]]:
    return []