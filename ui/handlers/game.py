from __future__ import annotations

import pygame

from core.game import Game
from core.save_io import save_game_to_file, load_game_from_file, export_record_to_file
from ui.controller import pixel_to_board
from ui.logic_click import handle_pending_auto_action_click, handle_board_phase_click
from ui.logic_menu import make_quit_confirm_dialog
from ui.logic_overlay import (
    handle_confirm_overlay_click,
    handle_slot_panel_click,
    handle_settings_panel_click,
    handle_game_over_overlay_click,
)


def handle_game_click(
    mx: int,
    my: int,
    win_mx: int,
    win_my: int,
    game: Game,
    overlay_button_rects: dict[str, pygame.Rect],
    system_button_rects: dict[str, pygame.Rect],
    quit_button_rect: pygame.Rect,
    confirm_dialog: dict[str, str] | None,
    confirm_action: str | None,
    settings_open: bool,
    settings_save_open: bool,
    settings_load_open: bool,
    record_open: bool,
    record_scroll: int,
    record_export_filename: str,
    save_slot_files: dict[int, str],
    arrow_hint_enabled: bool,
    preview_drop_enabled: bool,
    preview_eat_enabled: bool,
    preview_fire_enabled: bool,
    app_mode: str,
    menu_load_open: bool,
) -> dict:
    result: dict = {"running": True}

    if quit_button_rect.collidepoint(mx, my):
        result["confirm_dialog"] = make_quit_confirm_dialog()
        result["confirm_action"] = "quit"
        return result

    top_overlay = _get_top_overlay_name(
        confirm_dialog,
        app_mode,
        menu_load_open,
        settings_save_open,
        settings_load_open,
        settings_open,
        record_open,
    )

    if _close_overlay_from_outside(result, top_overlay, overlay_button_rects, mx, my):
        return result

    if game.game_over:
        return _handle_game_over_click(
            result,
            game,
            mx,
            my,
            overlay_button_rects,
            record_export_filename,
        )

    if confirm_dialog is not None:
        handled, action = handle_confirm_overlay_click(mx, my, overlay_button_rects, confirm_action)
        if handled:
            _dispatch_confirm_action(result, game, action)
            return result

    if settings_save_open:
        handled, action = handle_slot_panel_click(mx, my, overlay_button_rects, "save_slot")
        if handled:
            if action in {"outside", "cancel"}:
                result["settings_save_open"] = False
            elif action in {"1", "2", "3"}:
                _do_save(result, game, save_slot_files[int(action)], int(action))
            return result

    if settings_load_open:
        handled, action = handle_slot_panel_click(mx, my, overlay_button_rects, "load_slot")
        if handled:
            if action in {"outside", "cancel"}:
                result["settings_load_open"] = False
            elif action in {"1", "2", "3"}:
                _do_load(result, save_slot_files[int(action)], int(action))
            return result

    if settings_open:
        handled, action = handle_settings_panel_click(mx, my, overlay_button_rects)
        if handled:
            result.update(
                _dispatch_settings_action(
                    action,
                    game,
                    record_export_filename,
                    arrow_hint_enabled,
                    preview_drop_enabled,
                    preview_eat_enabled,
                    preview_fire_enabled,
                    record_open,
                )
            )
            return result

    if _handle_system_button_click(result, game, system_button_rects, mx, my):
        return result

    return _handle_board_click(result, game, win_mx, win_my)


def _get_top_overlay_name(
    confirm_dialog,
    app_mode,
    menu_load_open,
    settings_save_open,
    settings_load_open,
    settings_open,
    record_open,
) -> str | None:
    if confirm_dialog is not None:
        return "confirm"
    if app_mode == "menu" and menu_load_open:
        return "menu_load_slot"
    if settings_save_open:
        return "save_slot"
    if settings_load_open:
        return "load_slot"
    if settings_open:
        return "settings"
    if record_open:
        return "record"
    return None


def _close_overlay_from_outside(
    result: dict,
    top_overlay: str | None,
    overlay_button_rects: dict[str, pygame.Rect],
    mx: int,
    my: int,
) -> bool:
    close_map = {
        "confirm": ("confirm_panel", ("confirm_dialog", "confirm_action")),
        "save_slot": ("save_slot_panel", ("settings_save_open",)),
        "load_slot": ("load_slot_panel", ("settings_load_open",)),
        "settings": ("settings_panel", ("settings_open", "settings_save_open", "settings_load_open")),
        "record": ("record_panel", ("record_open",)),
    }

    if top_overlay not in close_map:
        return False

    panel_key, state_keys = close_map[top_overlay]
    panel_rect = overlay_button_rects.get(panel_key)
    if panel_rect is None or panel_rect.collidepoint(mx, my):
        return False

    for key in state_keys:
        result[key] = None if key in {"confirm_dialog", "confirm_action"} else False
    return True


def _handle_game_over_click(
    result: dict,
    game: Game,
    mx: int,
    my: int,
    overlay_button_rects: dict[str, pygame.Rect],
    record_export_filename: str,
) -> dict:
    handled, action = handle_game_over_overlay_click(mx, my, overlay_button_rects)
    if not handled:
        return result

    if action == "game_over_restart":
        result["enter_game"] = (Game(), "已重新开始对局。")
    elif action == "game_over_load":
        result["app_mode"] = "menu"
        result["menu_load_open"] = True
        result["reset_ui"] = True
        result["status_message"] = "请选择要载入的存档槽位。"
    elif action == "game_over_export":
        _do_export(result, game, record_export_filename)
    elif action == "game_over_quit":
        result["confirm_dialog"] = make_quit_confirm_dialog()
        result["confirm_action"] = "quit"

    return result


def _dispatch_confirm_action(result: dict, game: Game, action: str | None) -> None:
    if action == "close":
        result["confirm_dialog"] = None
        result["confirm_action"] = None
    elif action == "endgame":
        game.finish_by_agreement()
        result["status_message"] = "已确认终局。"
        result["confirm_dialog"] = None
        result["confirm_action"] = None
    elif action == "resign":
        game.resign()
        result["status_message"] = "已确认投降。"
        result["confirm_dialog"] = None
        result["confirm_action"] = None
    elif action == "restart":
        result["enter_game"] = (Game(), "已重新开始对局。")
        result["confirm_dialog"] = None
        result["confirm_action"] = None
    elif action == "quit":
        result["running"] = False


def _handle_system_button_click(
    result: dict,
    game: Game,
    system_button_rects: dict[str, pygame.Rect],
    mx: int,
    my: int,
) -> bool:
    for key, rect in system_button_rects.items():
        if not rect.collidepoint(mx, my):
            continue

        if key == "undo":
            _do_undo(result, game)
        elif key == "restart":
            result["confirm_dialog"] = {
                "title": "确认重新开始",
                "message": "是否确认重新开始对局？\n当前进度将丢失。",
            }
            result["confirm_action"] = "restart"
        elif key == "settings":
            result["settings_open"] = True
        elif key == "backtrack":
            _do_backtrack(result, game)
        return True

    return False


def _handle_board_click(result: dict, game: Game, win_mx: int, win_my: int) -> dict:
    hovered_cell = pixel_to_board(win_mx, win_my)
    if hovered_cell is None:
        return result

    if game.has_pending_auto_action():
        consumed, message, is_error = handle_pending_auto_action_click(game)
        if consumed:
            result["status_message"] = message
            result["status_is_error"] = is_error
            result["hovered_cell"] = None
            return result

    hx, hy = hovered_cell
    consumed, message, is_error = handle_board_phase_click(game, game.get_legal_actions(), hx, hy)
    if consumed:
        result["status_message"] = message
        result["status_is_error"] = is_error
        result["hovered_cell"] = None

    return result


def _do_undo(result: dict, game: Game) -> None:
    try:
        game.undo()
        result["clear_transient"] = True
        result["status_message"] = "已撤销上一步操作。"
    except Exception as e:
        result["status_message"] = f"撤销失败：{e}"
        result["status_is_error"] = True


def _do_backtrack(result: dict, game: Game) -> None:
    try:
        if game.phase == "drop":
            result["status_message"] = "当前已经处于落子阶段，无法继续回退。"
            result["status_is_error"] = True
            return

        start_player = game.current_player
        stepped = 0

        while game.can_undo():
            game.undo()
            stepped += 1

            if game.phase == "drop" and game.current_player == start_player:
                break

        game.clear_pending_auto_action()
        result["clear_transient"] = True
        result["status_message"] = f"已回退 {stepped} 步，回到落子阶段。"
    except Exception as e:
        result["status_message"] = f"回退失败：{e}"
        result["status_is_error"] = True


def _do_save(result: dict, game: Game, filename: str, slot: int) -> None:
    try:
        save_game_to_file(game, filename)
        result["status_message"] = f"已保存到槽位 {slot}"
        result["status_is_error"] = False
    except Exception as e:
        result["status_message"] = f"保存失败：{e}"
        result["status_is_error"] = True


def _do_load(result: dict, filename: str, slot: int) -> None:
    try:
        new_game = load_game_from_file(filename)
        result["game_replaced"] = new_game
        result["status_message"] = f"已从槽位 {slot} 读取存档"
        result["status_is_error"] = False
        result["settings_load_open"] = False
        result["settings_open"] = False
    except Exception as e:
        result["status_message"] = f"读档失败：{e}"
        result["status_is_error"] = True


def _do_export(result: dict, game: Game, filename: str) -> None:
    try:
        export_record_to_file(game, filename)
        result["status_message"] = f"已导出棋谱到 {filename}"
        result["status_is_error"] = False
    except Exception as e:
        result["status_message"] = f"导出失败：{e}"
        result["status_is_error"] = True


def _dispatch_settings_action(
    action: str | None,
    game: Game,
    record_export_filename: str,
    arrow_hint_enabled: bool,
    preview_drop_enabled: bool,
    preview_eat_enabled: bool,
    preview_fire_enabled: bool,
    record_open: bool,
) -> dict:
    result: dict = {}

    if action in (None, "outside", "close_settings"):
        result["settings_open"] = False
        result["settings_save_open"] = False
        result["settings_load_open"] = False
    elif action == "open_save_slots":
        result["settings_save_open"] = True
        result["settings_load_open"] = False
    elif action == "open_load_slots":
        result["settings_load_open"] = True
        result["settings_save_open"] = False
    elif action == "toggle_record":
        result["record_open"] = not record_open
        if not result["record_open"]:
            result["record_scroll"] = 0
        result["settings_open"] = False
        result["settings_save_open"] = False
        result["settings_load_open"] = False
    elif action == "toggle_arrow_hint":
        result["arrow_hint_enabled"] = not arrow_hint_enabled
    elif action == "toggle_preview_drop":
        result["preview_drop_enabled"] = not preview_drop_enabled
    elif action == "toggle_preview_eat":
        result["preview_eat_enabled"] = not preview_eat_enabled
    elif action == "toggle_preview_fire":
        result["preview_fire_enabled"] = not preview_fire_enabled
    elif action == "export_record":
        _do_export(result, game, record_export_filename)
    elif action == "endgame":
        result["confirm_dialog"] = {
            "title": "确认终局",
            "message": "是否确认双方同意结束当前对局？\n系统将按当前局面计算胜负。",
        }
        result["confirm_action"] = "endgame"
        result["settings_open"] = False
    elif action == "resign":
        result["confirm_dialog"] = {
            "title": "确认投降",
            "message": "是否确认当前行动方投降？\n确认后将直接判负。",
        }
        result["confirm_action"] = "resign"
        result["settings_open"] = False
    elif action == "quit_game":
        result["confirm_dialog"] = {
            "title": "确认退出",
            "message": "是否确认退出游戏？",
        }
        result["confirm_action"] = "quit"
        result["settings_open"] = False
        result["settings_save_open"] = False
        result["settings_load_open"] = False

    return result
