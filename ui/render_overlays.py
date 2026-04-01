#ui/render_overlays.py

from __future__ import annotations

from typing import Any
import pygame

from ui.constants import *
from ui.scale import ui
from ui.render_common import (
    draw_button,
    draw_card_panel,
    draw_danger_button,
    draw_multiline_text,
    draw_text,
    font_h,
)


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
    for line in visible:
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

    draw_text(
        surface,
        title,
        fonts["heading"],
        TEXT_COLOR,
        panel_rect.x + ui.x(CARD_TITLE_LEFT),
        panel_rect.y + ui.y(CARD_TITLE_TOP),
    )
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
        panel_rect.x + ui.x(130),
        panel_rect.bottom - ui.y(92),
        ui.x(200),
        ui.y(52),
    )
    confirm_rect = pygame.Rect(
        panel_rect.right - ui.x(330),
        panel_rect.bottom - ui.y(92),
        ui.x(200),
        ui.y(52),
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

    draw_text(
        surface,
        "设置",
        fonts["heading"],
        TEXT_COLOR,
        panel_rect.x + ui.x(CARD_TITLE_LEFT),
        panel_rect.y + ui.y(CARD_TITLE_TOP),
    )

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

    start_y = panel_rect.y + ui.y(92)
    for i, (key, text) in enumerate(labels):
        row = i // 2
        col = i % 2

        rect = pygame.Rect(
            panel_rect.x + ui.x(42) + col * ui.x(372),
            start_y + row * ui.y(58),
            ui.x(332),
            ui.y(CARD_BUTTON_HEIGHT),
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
        (LOGICAL_WIDTH - ui.x(SLOT_PANEL_WIDTH)) // 2,
        (LOGICAL_HEIGHT - ui.y(SLOT_PANEL_HEIGHT)) // 2,
        ui.x(SLOT_PANEL_WIDTH),
        ui.y(SLOT_PANEL_HEIGHT),
    )
    rects[f"{prefix}_panel"] = panel_rect
    draw_card_panel(surface, panel_rect, MODAL_BG, MODAL_BORDER)

    draw_text(
        surface,
        title,
        fonts["heading"],
        TEXT_COLOR,
        panel_rect.x + ui.x(CARD_TITLE_LEFT),
        panel_rect.y + ui.y(CARD_TITLE_TOP),
    )

    labels = [
        (f"{prefix}_1", "槽位 1"),
        (f"{prefix}_2", "槽位 2"),
        (f"{prefix}_3", "槽位 3"),
        (f"{prefix}_cancel", "取消"),
    ]

    for i, (key, text) in enumerate(labels):
        rect = pygame.Rect(
            panel_rect.centerx - ui.x(110),
            panel_rect.y + ui.y(92) + i * ui.y(56),
            ui.x(220),
            ui.y(44),
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
        (LOGICAL_WIDTH - ui.x(640)) // 2,
        (LOGICAL_HEIGHT - ui.y(460)) // 2,
        ui.x(640),
        ui.y(460),
    )
    rects["menu_panel"] = panel_rect
    draw_card_panel(surface, panel_rect, MODAL_BG, MODAL_BORDER)

    title_font = ui.font("microsoftyaheiui", 64, bold=True)
    subtitle_font = ui.font("microsoftyaheiui", 30, bold=True)

    title_img = title_font.render("炮棋", True, TEXT_COLOR)
    title_rect = title_img.get_rect(center=(panel_rect.centerx, panel_rect.y + ui.y(84)))
    surface.blit(title_img, title_rect)

    subtitle_img = subtitle_font.render("桌面版", True, TEXT_COLOR)
    subtitle_rect = subtitle_img.get_rect(center=(panel_rect.centerx, panel_rect.y + ui.y(156)))
    surface.blit(subtitle_img, subtitle_rect)

    start_rect = pygame.Rect(
        0,
        panel_rect.y + ui.y(220),
        ui.x(CARD_BUTTON_WIDTH),
        ui.y(56),
    )
    start_rect.centerx = panel_rect.centerx

    load_rect = pygame.Rect(
        0,
        panel_rect.y + ui.y(292),
        ui.x(CARD_BUTTON_WIDTH),
        ui.y(56),
    )
    load_rect.centerx = panel_rect.centerx

    quit_rect = pygame.Rect(
        0,
        panel_rect.y + ui.y(364),
        ui.x(CARD_BUTTON_WIDTH),
        ui.y(56),
    )
    quit_rect.centerx = panel_rect.centerx

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

    panel_rect = pygame.Rect(
        LOGICAL_WIDTH // 2 - ui.x(GAME_OVER_PANEL_WIDTH) // 2,
        LOGICAL_HEIGHT // 2 - ui.y(GAME_OVER_PANEL_HEIGHT) // 2,
        ui.x(GAME_OVER_PANEL_WIDTH),
        ui.y(GAME_OVER_PANEL_HEIGHT),
    )
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

    draw_text(surface, title, big_title_font, color, panel_rect.x + ui.x(40), panel_rect.y + ui.y(34))
    draw_text(surface, "请选择下方操作：", big_body_font, TEXT_COLOR, panel_rect.x + ui.x(40), panel_rect.y + ui.y(106))

    restart_rect = pygame.Rect(panel_rect.x + ui.x(24), panel_rect.y + ui.y(188), ui.x(138), ui.y(50))
    load_rect = pygame.Rect(panel_rect.x + ui.x(174), panel_rect.y + ui.y(188), ui.x(138), ui.y(50))
    export_rect = pygame.Rect(panel_rect.x + ui.x(324), panel_rect.y + ui.y(188), ui.x(138), ui.y(50))
    quit_rect = pygame.Rect(panel_rect.x + ui.x(474), panel_rect.y + ui.y(188), ui.x(138), ui.y(50))

    draw_button(surface, "重开", restart_rect, fonts, hovered=(mouse_pos is not None and restart_rect.collidepoint(mouse_pos)))
    draw_button(surface, "载入", load_rect, fonts, hovered=(mouse_pos is not None and load_rect.collidepoint(mouse_pos)))
    draw_button(surface, "导出棋谱", export_rect, fonts, hovered=(mouse_pos is not None and export_rect.collidepoint(mouse_pos)))
    draw_danger_button(surface, "退出游戏", quit_rect, fonts, hovered=(mouse_pos is not None and quit_rect.collidepoint(mouse_pos)))

    rects["game_over_restart"] = restart_rect
    rects["game_over_load"] = load_rect
    rects["game_over_export"] = export_rect
    rects["game_over_quit"] = quit_rect

    return rects