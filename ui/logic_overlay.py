#ui/logic_overlay.py
from __future__ import annotations

import pygame


def _clicked_outside_panel(
    overlay_button_rects: dict[str, pygame.Rect],
    panel_key: str,
    mx: int,
    my: int,
) -> bool:
    panel_rect = overlay_button_rects.get(panel_key)
    return panel_rect is not None and not panel_rect.collidepoint(mx, my)


def handle_confirm_overlay_click(
    mx: int,
    my: int,
    overlay_button_rects: dict[str, pygame.Rect],
    confirm_action: str | None,
) -> tuple[bool, str | None]:
    if _clicked_outside_panel(overlay_button_rects, "confirm_panel", mx, my):
        return True, "close"

    if "cancel" in overlay_button_rects and overlay_button_rects["cancel"].collidepoint(mx, my):
        return True, "close"

    if "confirm" in overlay_button_rects and overlay_button_rects["confirm"].collidepoint(mx, my):
        return True, confirm_action

    if "confirm_panel" in overlay_button_rects:
        return True, None

    return False, None


def handle_record_panel_click(
    mx: int,
    my: int,
    overlay_button_rects: dict[str, pygame.Rect],
    record_scroll: int,
    history_len: int,
    lines_per_page: int,
) -> tuple[bool, int, bool]:
    if _clicked_outside_panel(overlay_button_rects, "record_panel", mx, my):
        return True, record_scroll, True

    if "record_up" in overlay_button_rects and overlay_button_rects["record_up"].collidepoint(mx, my):
        return True, max(0, record_scroll - 1), False

    if "record_down" in overlay_button_rects and overlay_button_rects["record_down"].collidepoint(mx, my):
        total_pages = max(1, (history_len + lines_per_page - 1) // lines_per_page)
        return True, min(total_pages - 1, record_scroll + 1), False

    if "record_panel" in overlay_button_rects:
        return True, record_scroll, False

    return False, record_scroll, False


def handle_slot_panel_click(
    mx: int,
    my: int,
    overlay_button_rects: dict[str, pygame.Rect],
    prefix: str,
) -> tuple[bool, str | None]:
    panel_key = f"{prefix}_panel"
    if _clicked_outside_panel(overlay_button_rects, panel_key, mx, my):
        return True, "outside"

    for slot in ("1", "2", "3"):
        key = f"{prefix}_{slot}"
        if key in overlay_button_rects and overlay_button_rects[key].collidepoint(mx, my):
            return True, slot

    cancel_key = f"{prefix}_cancel"
    if cancel_key in overlay_button_rects and overlay_button_rects[cancel_key].collidepoint(mx, my):
        return True, "cancel"

    if panel_key in overlay_button_rects:
        return True, None

    return False, None


def handle_settings_panel_click(
    mx: int,
    my: int,
    overlay_button_rects: dict[str, pygame.Rect],
) -> tuple[bool, str | None]:
    if _clicked_outside_panel(overlay_button_rects, "settings_panel", mx, my):
        return True, "outside"

    keys = [
        "open_save_slots",
        "open_load_slots",
        "toggle_record",
        "toggle_arrow_hint",
        "toggle_preview_drop",
        "toggle_preview_eat",
        "toggle_preview_fire",
        "export_record",
        "endgame",
        "resign",
        "close_settings",
        "quit_game",
    ]

    for key in keys:
        if key in overlay_button_rects and overlay_button_rects[key].collidepoint(mx, my):
            return True, key

    if "settings_panel" in overlay_button_rects:
        return True, None

    return False, None


def handle_game_over_overlay_click(
    mx: int,
    my: int,
    overlay_button_rects: dict[str, pygame.Rect],
) -> tuple[bool, str | None]:
    keys = [
        "game_over_restart",
        "game_over_load",
        "game_over_export",
        "game_over_quit",
    ]

    for key in keys:
        if key in overlay_button_rects and overlay_button_rects[key].collidepoint(mx, my):
            return True, key

    if "game_over_panel" in overlay_button_rects:
        return True, None

    return False, None