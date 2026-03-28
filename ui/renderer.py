# ui/renderer.py

from __future__ import annotations

import pygame
from typing import Any

from ui.constants import *

def make_fonts() -> dict[str, pygame.font.Font]:
    return {
        "title": pygame.font.SysFont("microsoftyaheiui", 20, bold=True),
        "heading": pygame.font.SysFont("microsoftyaheiui", 15, bold=True),
        "body": pygame.font.SysFont("microsoftyaheiui", 13),
        "small": pygame.font.SysFont("microsoftyaheiui", 11),
        "piece": pygame.font.SysFont("arial", 18, bold=True),
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


def cell_rect(x: int, y: int) -> pygame.Rect:
    px = BOARD_ORIGIN_X + (x - 1) * CELL_SIZE
    py = BOARD_ORIGIN_Y + (y - 1) * CELL_SIZE
    return pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)

def cell_center(x: int, y: int) -> tuple[int, int]:
    rect = cell_rect(x, y)
    return rect.centerx, rect.centery

def draw_capturable_targets(
    surface: pygame.Surface,
    capturable_cells: list[tuple[int, int]],
) -> None:
    for x, y in capturable_cells:
        rect = cell_rect(x, y)
        inner = rect.inflate(-10, -10)
        pygame.draw.rect(surface, CAPTURABLE_COLOR, inner, 3, border_radius=8)


def draw_cannon_highlights(
    surface: pygame.Surface,
    cannon_infos: list[dict[str, Any]],
    color: tuple[int, int, int],
) -> None:
    """
    根据 action 里附带的 cannon 快照，画出整条炮管。
    这里假定 positions 是一串格子坐标。
    """
    for info in cannon_infos:
        cannon = info.get("cannon", {})
        positions = cannon.get("positions", [])

        centers: list[tuple[int, int]] = []
        for pos in positions:
            x = pos.get("x")
            y = pos.get("y")
            if isinstance(x, int) and isinstance(y, int):
                centers.append(cell_center(x, y))

                rect = cell_rect(x, y)
                inner = rect.inflate(-6, -6)
                pygame.draw.rect(surface, color, inner, 3, border_radius=8)

        if len(centers) >= 2:
            pygame.draw.lines(surface, color, False, centers, 4)

def draw_board(
    surface: pygame.Surface,
    board_data: list[list[dict[str, Any] | None]],
    legal_highlights: dict[tuple[int, int], str],
    capturable_cells: list[tuple[int, int]],
    cannon_highlights: list[dict[str, Any]],
    hover_cannon_highlights: list[dict[str, Any]],
    fonts: dict[str, pygame.font.Font],
) -> None:
    board_rect = pygame.Rect(
        BOARD_ORIGIN_X,
        BOARD_ORIGIN_Y,
        BOARD_PIXEL_SIZE,
        BOARD_PIXEL_SIZE,
    )

    pygame.draw.rect(surface, BOARD_BG, board_rect)
    pygame.draw.rect(surface, GRID_COLOR, board_rect, 2)

    # 高亮合法格
    for (x, y), mode in legal_highlights.items():
        rect = cell_rect(x, y)
        if mode == "place":
            color = LEGAL_PLACE_COLOR
        else:
            color = LEGAL_UPGRADE_COLOR
        pygame.draw.rect(surface, color, rect, 4, border_radius=8)

    # 网格线
    for i in range(BOARD_SIZE + 1):
        px = BOARD_ORIGIN_X + i * CELL_SIZE
        py = BOARD_ORIGIN_Y + i * CELL_SIZE

        pygame.draw.line(
            surface,
            GRID_COLOR,
            (px, BOARD_ORIGIN_Y),
            (px, BOARD_ORIGIN_Y + BOARD_PIXEL_SIZE),
            1,
        )
        pygame.draw.line(
            surface,
            GRID_COLOR,
            (BOARD_ORIGIN_X, py),
            (BOARD_ORIGIN_X + BOARD_PIXEL_SIZE, py),
            1,
        )

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
            BOARD_ORIGIN_X + i * CELL_SIZE + CELL_SIZE // 2 - 5,
            BOARD_ORIGIN_Y - 24,
        )
        draw_text(
            surface,
            label,
            fonts["small"],
            TEXT_COLOR,
            BOARD_ORIGIN_X - 24,
            BOARD_ORIGIN_Y + i * CELL_SIZE + CELL_SIZE // 2 - 8,
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
            radius = CELL_SIZE // 2 - 8

            fill = RED_PIECE if color == "R" else BLUE_PIECE
            pygame.draw.circle(surface, fill, (cx, cy), radius)
            pygame.draw.circle(surface, GRID_COLOR, (cx, cy), radius, 2)

            txt = fonts["piece"].render(str(level), True, PIECE_TEXT)
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

    txt = fonts["body"].render(text, True, BUTTON_TEXT)
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
            width,
            ACTION_BUTTON_HEIGHT,
        )

        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        draw_button(surface, action.get("label", str(action)), rect, fonts, hovered=hovered)

        button_items.append((rect, action))
        y += ACTION_BUTTON_HEIGHT + ACTION_BUTTON_GAP

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
            start_x + col * (SYSTEM_BUTTON_WIDTH + SYSTEM_BUTTON_GAP),
            start_y + row * (SYSTEM_BUTTON_HEIGHT + SYSTEM_BUTTON_GAP),
            SYSTEM_BUTTON_WIDTH,
            SYSTEM_BUTTON_HEIGHT,
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

    rect = pygame.Rect(x, y, 120, 24)
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

    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_BG)
    surface.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 70, 300, 140)
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

    draw_text(surface, title, fonts["heading"], color, panel_rect.x + 28, panel_rect.y + 24)
    draw_text(surface, "可点击 Restart / Load / Quit", fonts["body"], TEXT_COLOR, panel_rect.x + 28, panel_rect.y + 62)

def draw_panel(
    surface: pygame.Surface,
    snapshot: dict[str, Any],
    status_message: str,
    status_is_error: bool,
    fonts: dict[str, pygame.font.Font],
    mouse_pos: tuple[int, int] | None,
) -> tuple[list[tuple[pygame.Rect, dict[str, Any]]], dict[str, pygame.Rect]]:
    panel_rect = pygame.Rect(
        SIDEBAR_X,
        SIDEBAR_Y,
        SIDEBAR_WIDTH,
        SIDEBAR_HEIGHT,
    )
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, 2, border_radius=12)

    phase_info = snapshot.get("phase_info", {})
    logs = snapshot.get("logs", {})
    legal_info = snapshot.get("legal_actions", {})
    actions = legal_info.get("actions", [])

    left_x = SIDEBAR_X + 16
    right_x = SIDEBAR_X + 275
    y = SIDEBAR_Y + 14

    # 标题
    draw_text(surface, "炮棋 Pygame UI", fonts["title"], TEXT_COLOR, left_x, y)
    draw_phase_badge(
        surface,
        phase_info.get("phase", ""),
        phase_info.get("phase_name", ""),
        right_x + 95,
        y + 1,
        fonts,
    )
    y += 32

    # 基本状态
    current_player = phase_info.get("current_player", "")
    current_player_name = phase_info.get("current_player_name", current_player)
    player_color = RED_PIECE if current_player == "R" else BLUE_PIECE

    draw_text(surface, "当前玩家：", fonts["body"], TEXT_COLOR, left_x, y)
    draw_text(surface, current_player_name, fonts["body"], player_color, left_x + 74, y)
    y += 22

    draw_text(
        surface,
        f"当前阶段：{phase_info.get('phase_name', phase_info.get('phase', ''))}",
        fonts["body"],
        TEXT_COLOR,
        left_x,
        y,
    )
    y += 22

    draw_text(
        surface,
        f"回合数：{phase_info.get('turn_number', '')}",
        fonts["body"],
        TEXT_COLOR,
        left_x,
        y,
    )
    y += 22

    draw_text(
        surface,
        f"合法动作：{legal_info.get('count', 0)}",
        fonts["body"],
        TEXT_COLOR,
        left_x,
        y,
    )
    y += 24

    # 最近动作
    history = logs.get("history", [])
    last_record = history[-1] if history else "（暂无）"

    draw_text(surface, "最近动作", fonts["heading"], TEXT_COLOR, left_x, y)
    y += 18
    draw_multiline_text(
        surface,
        last_record,
        fonts["small"],
        TEXT_COLOR,
        left_x,
        y,
        line_gap=3,
        max_lines=2,
    )
    y += 34

    # 提示
    draw_text(surface, "提示", fonts["heading"], TEXT_COLOR, left_x, y)
    y += 18

    status_color = STATUS_ERR if status_is_error else STATUS_OK
    draw_multiline_text(
        surface,
        status_message or "请选择一个合法动作。",
        fonts["small"],
        status_color,
        left_x,
        y,
        line_gap=3,
        max_lines=3,
    )
    y += 46

    # 当前可执行动作
    draw_text(surface, "当前可执行动作", fonts["heading"], TEXT_COLOR, left_x, y)
    y += 18

    action_button_items, action_end_y = draw_action_buttons(
        surface,
        actions,
        fonts,
        start_x=left_x,
        start_y=y,
        width=220,
        mouse_pos=mouse_pos,
    )

    # 系统按钮放右侧，与动作区顶部对齐
    draw_text(surface, "系统操作", fonts["heading"], TEXT_COLOR, right_x, y - 18)
    system_button_rects, _ = draw_system_buttons(
        surface,
        fonts,
        start_x=right_x,
        start_y=y,
        mouse_pos=mouse_pos,
    )

    # 最近棋谱放在动作按钮区下方
    history_y = action_end_y + 14
    draw_text(surface, "最近棋谱", fonts["heading"], TEXT_COLOR, left_x, history_y)
    history_y += 18

    history_text = "\n".join(history[-4:]) if history else "（暂无）"
    draw_multiline_text(
        surface,
        history_text,
        fonts["small"],
        TEXT_COLOR,
        left_x,
        history_y,
        line_gap=3,
        max_lines=4,
    )

    # 退出按钮固定放右下角
    quit_rect = pygame.Rect(
        QUIT_BUTTON_X,
        QUIT_BUTTON_Y,
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
    return pygame.Rect(
        QUIT_BUTTON_X,
        QUIT_BUTTON_Y,
        QUIT_BUTTON_WIDTH,
        QUIT_BUTTON_HEIGHT,
    )

def get_action_button_rects_placeholder() -> list[tuple[pygame.Rect, dict[str, Any]]]:
    return []