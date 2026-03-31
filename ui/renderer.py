# ui/renderer.py

from __future__ import annotations

from typing import Any
import pygame

from ui.constants import *
from ui.render_common import make_fonts
from ui.render_overlays import (
    draw_confirm_modal,
    draw_game_over_overlay,
    draw_main_menu,
    draw_record_panel,
    draw_settings_panel,
    draw_slot_panel,
)
from ui.render_board import draw_board
from ui.render_sidebar import draw_panel, get_quit_button_rect

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

        if confirm_dialog is not None:
            overlay_buttons.update(
                draw_confirm_modal(
                    surface,
                    confirm_dialog["title"],
                    confirm_dialog["message"],
                    fonts,
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

    if settings_open and settings_save_open:
        overlay_buttons.update(
            draw_slot_panel(
                surface,
                "选择保存槽位",
                fonts,
                mouse_pos,
                "save_slot",
            )
        )

    if settings_open and settings_load_open:
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

def get_action_button_rects_placeholder() -> list[tuple[pygame.Rect, dict[str, Any]]]:
    return []