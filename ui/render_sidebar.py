#ui/render_sidebar.py

from __future__ import annotations

from typing import Any
import pygame

from ui.constants import *
from ui.scale import ui
from ui.render_common import (
    draw_button,
    draw_multiline_text,
    draw_text,
    font_h,
    multiline_block_height,
)

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

def get_quit_button_rect() -> pygame.Rect:
    return ui.rect(
        SIDEBAR_X + 730,
        SIDEBAR_Y + 868,
        QUIT_BUTTON_WIDTH,
        QUIT_BUTTON_HEIGHT,
    )