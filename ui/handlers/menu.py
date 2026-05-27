from __future__ import annotations

import pygame

from ui.logic_menu import make_quit_confirm_dialog, start_new_game_session, load_game_from_slot


def handle_menu_click(
    mx: int,
    my: int,
    overlay_button_rects: dict[str, pygame.Rect],
    confirm_dialog: dict[str, str] | None,
    confirm_action: str | None,
    menu_load_open: bool,
    save_slot_files: dict[int, str],
) -> dict:
    result: dict = {"running": True, "menu_load_open": menu_load_open}

    if confirm_dialog is not None:
        panel_rect = overlay_button_rects.get("confirm_panel")
        if panel_rect is not None and not panel_rect.collidepoint(mx, my):
            result["confirm_dialog"] = None
            result["confirm_action"] = None
            return result

        if "cancel" in overlay_button_rects and overlay_button_rects["cancel"].collidepoint(mx, my):
            result["confirm_dialog"] = None
            result["confirm_action"] = None
            return result

        if "confirm" in overlay_button_rects and overlay_button_rects["confirm"].collidepoint(mx, my):
            if confirm_action == "quit":
                result["running"] = False
                return result

            result["confirm_dialog"] = None
            result["confirm_action"] = None
            return result

        return result

    if menu_load_open:
        panel_rect = overlay_button_rects.get("menu_load_slot_panel")
        if panel_rect is not None and not panel_rect.collidepoint(mx, my):
            result["menu_load_open"] = False
            return result

        for slot_num in (1, 2, 3):
            key = f"menu_load_slot_{slot_num}"
            if key in overlay_button_rects and overlay_button_rects[key].collidepoint(mx, my):
                loaded_game, message, is_error = load_game_from_slot(save_slot_files, slot_num)
                if loaded_game is not None:
                    result["enter_game"] = (loaded_game, message)
                else:
                    result["status_message"] = message
                    result["status_is_error"] = is_error
                return result

        if (
            "menu_load_slot_cancel" in overlay_button_rects
            and overlay_button_rects["menu_load_slot_cancel"].collidepoint(mx, my)
        ):
            result["menu_load_open"] = False
            return result

        return result

    if "menu_start" in overlay_button_rects and overlay_button_rects["menu_start"].collidepoint(mx, my):
        new_game, message = start_new_game_session()
        result["enter_game"] = (new_game, message)
        return result

    if "menu_load" in overlay_button_rects and overlay_button_rects["menu_load"].collidepoint(mx, my):
        result["menu_load_open"] = True
        return result

    if "menu_quit" in overlay_button_rects and overlay_button_rects["menu_quit"].collidepoint(mx, my):
        result["confirm_dialog"] = make_quit_confirm_dialog()
        result["confirm_action"] = "quit"
        return result

    return result
