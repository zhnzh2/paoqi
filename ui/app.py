# ui/app.py

from __future__ import annotations

import pygame

from core.game import Game
from ui.constants import WINDOW_WIDTH, WINDOW_HEIGHT, LOGICAL_WIDTH, LOGICAL_HEIGHT, FPS
from ui.controller import (
    pixel_to_board,
    window_to_logical,
    get_hovered_drop_highlights,
    get_hovered_eat_cells,
    get_hovered_fire_cannons,
    get_capturable_highlights,
    get_fire_cannon_highlights,
)
from ui.renderer import make_fonts, render_all, get_quit_button_rect
from ui.save_io import save_game_to_file, load_game_from_file, export_record_to_file
from ui.logic_menu import make_quit_confirm_dialog, start_new_game_session, load_game_from_slot
from ui.logic_overlay import (
    handle_confirm_overlay_click,
    handle_record_panel_click,
    handle_slot_panel_click,
    handle_settings_panel_click,
    handle_game_over_overlay_click,
)
from ui.logic_click import handle_pending_auto_action_click, handle_board_phase_click
from ui.logic_preview import compute_preview_board_data

def run_app() -> None:
    pygame.init()
    pygame.display.set_caption("炮棋（桌面版测试界面）")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), vsync=1)
    clock = pygame.time.Clock()
    fonts = make_fonts()
    quit_button_rect = get_quit_button_rect()
    system_button_rects: dict[str, pygame.Rect] = {}
    save_slot_files = {
        1: "save_slot_1.json",
        2: "save_slot_2.json",
        3: "save_slot_3.json",
    }
    record_export_filename = "record_export.txt"
    mouse_pos: tuple[int, int] | None = None
    hovered_cell: tuple[int, int] | None = None

    record_open = False
    record_scroll = 0
    overlay_button_rects: dict[str, pygame.Rect] = {}
    confirm_dialog: dict[str, str] | None = None
    confirm_action: str | None = None
    settings_open = False
    arrow_hint_enabled = True
    preview_drop_enabled = True
    preview_eat_enabled = True
    preview_fire_enabled = True
    preview_board_data: list[list[dict | None]] | None = None

    app_mode = "menu"   # "menu" 或 "game"
    menu_load_open = False
    settings_save_open = False
    settings_load_open = False

    game = Game()
    status_message = ""
    status_is_error = False

    def get_top_overlay_name() -> str | None:
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

    def reset_ui_runtime_state() -> None:
        nonlocal menu_load_open
        nonlocal settings_open, settings_save_open, settings_load_open
        nonlocal record_open, record_scroll
        nonlocal hovered_cell, preview_board_data
        nonlocal confirm_dialog, confirm_action

        menu_load_open = False
        settings_open = False
        settings_save_open = False
        settings_load_open = False
        record_open = False
        record_scroll = 0
        hovered_cell = None
        preview_board_data = None
        confirm_dialog = None
        confirm_action = None

    def enter_game_with(new_game: Game, message: str) -> None:
        nonlocal game, app_mode, status_message, status_is_error

        game = new_game
        app_mode = "game"
        reset_ui_runtime_state()
        status_message = message
        status_is_error = False

    def open_quit_confirm() -> None:
        nonlocal confirm_dialog, confirm_action

        confirm_dialog = make_quit_confirm_dialog()
        confirm_action = "quit"

    def clear_transient_ui_state() -> None:
        nonlocal hovered_cell, preview_board_data
        nonlocal confirm_dialog, confirm_action
        nonlocal record_open

        hovered_cell = None
        preview_board_data = None
        confirm_dialog = None
        confirm_action = None
        record_open = False

    def save_to_slot(slot: int) -> None:
        nonlocal status_message, status_is_error

        try:
            save_game_to_file(game, save_slot_files[slot])
            status_message = f"已保存到槽位 {slot}"
            status_is_error = False
        except Exception as e:
            status_message = f"保存失败：{e}"
            status_is_error = True

    def load_from_slot_in_game(slot: int, close_settings: bool = True) -> None:
        nonlocal game, status_message, status_is_error
        nonlocal settings_open, settings_load_open

        try:
            game = load_game_from_file(save_slot_files[slot])
            status_message = f"已从槽位 {slot} 读取存档"
            status_is_error = False

            if close_settings:
                settings_load_open = False
                settings_open = False
        except Exception as e:
            status_message = f"读档失败：{e}"
            status_is_error = True

    running = True
    while running:
        if app_mode == "game" and not game.game_over:
            game.check_game_over_at_turn_start()
        snapshot = game.get_state_snapshot()
        mouse_pos = window_to_logical(*pygame.mouse.get_pos())
        legal_actions = game.get_legal_actions()
        if game.has_pending_auto_action() and game.pending_auto_message:
            status_message = game.pending_auto_message
            status_is_error = False

        capturable_cells = get_capturable_highlights(legal_actions) if game.phase == "eat" else []
        cannon_highlights = get_fire_cannon_highlights(legal_actions) if game.phase in {"fire", "muzzle"} else []

        legal_highlights = get_hovered_drop_highlights(legal_actions, hovered_cell) if game.phase == "drop" else {}
        hovered_eat_cells = get_hovered_eat_cells(legal_actions, hovered_cell) if game.phase == "eat" else []
        hovered_cannon_highlights = get_hovered_fire_cannons(legal_actions, hovered_cell) if game.phase in {"fire", "muzzle"} else []

        top_overlay = get_top_overlay_name()
        if top_overlay is not None:
            legal_highlights = {}
            capturable_cells = []
            cannon_highlights = []
            hovered_eat_cells = []
            hovered_cannon_highlights = []
            hovered_cell = None
            preview_board_data = None

        if game.has_pending_auto_action():
            pending = game.pending_auto_action

            if pending is not None:
                if pending.get("type") == "eat":
                    x = pending.get("x")
                    y = pending.get("y")
                    if isinstance(x, int) and isinstance(y, int):
                        capturable_cells = [(x, y)]
                        hovered_eat_cells = [(x, y)]

                elif pending.get("type") == "fire":
                    cannon = pending.get("cannon")
                    if isinstance(cannon, dict):
                        cannon_info = {
                            "type": pending.get("type"),
                            "index": pending.get("index"),
                            "direction": pending.get("direction"),
                            "cannon": cannon,
                            "label": pending.get("label", ""),
                        }
                        cannon_highlights = [cannon_info]
                        hovered_cannon_highlights = [cannon_info]

        preview_board_data = None

        if app_mode == "game" and top_overlay is None:
            preview_board_data = compute_preview_board_data(
                game,
                legal_actions,
                hovered_cell,
                preview_drop_enabled,
                preview_eat_enabled,
                preview_fire_enabled,
            )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if app_mode == "menu":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                elif event.type == pygame.MOUSEMOTION:
                    win_mx, win_my = event.pos
                    mouse_pos = window_to_logical(win_mx, win_my)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    win_mx, win_my = event.pos
                    mx, my = window_to_logical(win_mx, win_my)

                    if confirm_dialog is not None:
                        panel_rect = overlay_button_rects.get("confirm_panel")
                        if panel_rect is not None and not panel_rect.collidepoint(mx, my):
                            confirm_dialog = None
                            confirm_action = None
                            continue

                        if "cancel" in overlay_button_rects and overlay_button_rects["cancel"].collidepoint(mx, my):
                            confirm_dialog = None
                            confirm_action = None
                            continue

                        if "confirm" in overlay_button_rects and overlay_button_rects["confirm"].collidepoint(mx, my):
                            if confirm_action == "quit":
                                running = False
                                continue

                            confirm_dialog = None
                            confirm_action = None
                            continue

                        continue

                    if menu_load_open:
                        panel_rect = overlay_button_rects.get("menu_load_slot_panel")
                        if panel_rect is not None and not panel_rect.collidepoint(mx, my):
                            menu_load_open = False
                            continue

                        if "menu_load_slot_1" in overlay_button_rects and overlay_button_rects["menu_load_slot_1"].collidepoint(mx, my):
                            loaded_game, message, is_error = load_game_from_slot(save_slot_files, 1)
                            if loaded_game is not None:
                                enter_game_with(loaded_game, message)
                            else:
                                status_message = message
                                status_is_error = is_error
                            continue

                        if "menu_load_slot_2" in overlay_button_rects and overlay_button_rects["menu_load_slot_2"].collidepoint(mx, my):
                            loaded_game, message, is_error = load_game_from_slot(save_slot_files, 2)
                            if loaded_game is not None:
                                enter_game_with(loaded_game, message)
                            else:
                                status_message = message
                                status_is_error = is_error
                            continue

                        if "menu_load_slot_3" in overlay_button_rects and overlay_button_rects["menu_load_slot_3"].collidepoint(mx, my):
                            loaded_game, message, is_error = load_game_from_slot(save_slot_files, 3)
                            if loaded_game is not None:
                                enter_game_with(loaded_game, message)
                            else:
                                status_message = message
                                status_is_error = is_error
                            continue

                        if "menu_load_slot_cancel" in overlay_button_rects and overlay_button_rects["menu_load_slot_cancel"].collidepoint(mx, my):
                            menu_load_open = False
                            continue

                        continue

                    if "menu_start" in overlay_button_rects and overlay_button_rects["menu_start"].collidepoint(mx, my):
                        new_game, message = start_new_game_session()
                        enter_game_with(new_game, message)
                        continue

                    if "menu_load" in overlay_button_rects and overlay_button_rects["menu_load"].collidepoint(mx, my):
                        menu_load_open = True
                        continue

                    if "menu_quit" in overlay_button_rects and overlay_button_rects["menu_quit"].collidepoint(mx, my):
                        open_quit_confirm()
                        continue

                continue

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_u:
                    try:
                        game.undo()
                        game.clear_pending_auto_action()
                        hovered_cell = None
                        confirm_dialog = None
                        confirm_action = None
                        record_open = False
                        status_message = "已撤销上一步操作。"
                        status_is_error = False
                    except Exception as e:
                        status_message = f"撤销失败：{e}"
                        status_is_error = True

                elif event.key == pygame.K_r:
                    game = Game()
                    status_message = "已重新开始对局。"
                    status_is_error = False

            elif event.type == pygame.MOUSEMOTION:
                win_mx, win_my = event.pos
                mouse_pos = window_to_logical(win_mx, win_my)

                if get_top_overlay_name() is not None:
                    hovered_cell = None
                else:
                    hovered_cell = pixel_to_board(win_mx, win_my)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                win_mx, win_my = event.pos
                mx, my = window_to_logical(win_mx, win_my)

                if quit_button_rect.collidepoint(mx, my):
                    open_quit_confirm()
                    continue
                top_overlay = get_top_overlay_name()

                if top_overlay == "confirm":
                    panel_rect = overlay_button_rects.get("confirm_panel")
                    if panel_rect is not None and not panel_rect.collidepoint(mx, my):
                        confirm_dialog = None
                        confirm_action = None
                        continue

                elif top_overlay == "save_slot":
                    panel_rect = overlay_button_rects.get("save_slot_panel")
                    if panel_rect is not None and not panel_rect.collidepoint(mx, my):
                        settings_save_open = False
                        continue

                elif top_overlay == "load_slot":
                    panel_rect = overlay_button_rects.get("load_slot_panel")
                    if panel_rect is not None and not panel_rect.collidepoint(mx, my):
                        settings_load_open = False
                        continue

                elif top_overlay == "settings":
                    panel_rect = overlay_button_rects.get("settings_panel")
                    if panel_rect is not None and not panel_rect.collidepoint(mx, my):
                        settings_open = False
                        settings_save_open = False
                        settings_load_open = False
                        continue

                elif top_overlay == "record":
                    panel_rect = overlay_button_rects.get("record_panel")
                    if panel_rect is not None and not panel_rect.collidepoint(mx, my):
                        record_open = False
                        continue

                if game.game_over:
                    handled, action = handle_game_over_overlay_click(
                        mx,
                        my,
                        overlay_button_rects,
                    )

                    if handled:
                        if action == "game_over_restart":
                            enter_game_with(Game(), "已重新开始对局。")
                            continue

                        if action == "game_over_load":
                            app_mode = "menu"
                            menu_load_open = True
                            record_open = False
                            record_scroll = 0
                            settings_open = False
                            settings_save_open = False
                            settings_load_open = False
                            hovered_cell = None
                            preview_board_data = None
                            confirm_dialog = None
                            confirm_action = None
                            status_message = "请选择要载入的存档槽位。"
                            status_is_error = False
                            continue

                        if action == "game_over_export":
                            try:
                                export_record_to_file(game, record_export_filename)
                                status_message = f"已导出棋谱到 {record_export_filename}"
                                status_is_error = False
                            except Exception as e:
                                status_message = f"导出失败：{e}"
                                status_is_error = True
                            continue

                        if action == "game_over_quit":
                            open_quit_confirm()
                            continue

                        continue

                if confirm_dialog is not None:
                    handled, action = handle_confirm_overlay_click(mx, my, overlay_button_rects, confirm_action)

                    if handled:
                        if action == "close":
                            confirm_dialog = None
                            confirm_action = None
                            continue

                        if action == "endgame":
                            game.finish_by_agreement()
                            status_message = "已确认终局。"
                            status_is_error = False
                            confirm_dialog = None
                            confirm_action = None
                            continue

                        if action == "resign":
                            game.resign()
                            status_message = "已确认投降。"
                            status_is_error = False
                            confirm_dialog = None
                            confirm_action = None
                            continue

                        if action == "quit":
                            running = False
                            continue

                        continue

                if settings_save_open:
                    handled, action = handle_slot_panel_click(mx, my, overlay_button_rects, "save_slot")

                    if handled:
                        if action == "outside" or action == "cancel":
                            settings_save_open = False
                            continue

                        if action in {"1", "2", "3"}:
                            save_to_slot(int(action))
                            continue

                        continue

                if settings_load_open:
                    handled, action = handle_slot_panel_click(mx, my, overlay_button_rects, "load_slot")

                    if handled:
                        if action == "outside" or action == "cancel":
                            settings_load_open = False
                            continue

                        if action in {"1", "2", "3"}:
                            load_from_slot_in_game(int(action), close_settings=True)
                            continue

                        continue

                if settings_open:
                    handled, action = handle_settings_panel_click(mx, my, overlay_button_rects)

                    if handled:
                        if action == "outside" or action == "close_settings":
                            settings_open = False
                            settings_save_open = False
                            settings_load_open = False
                            continue

                        if action == "open_save_slots":
                            settings_save_open = True
                            settings_load_open = False
                            continue

                        if action == "open_load_slots":
                            settings_load_open = True
                            settings_save_open = False
                            continue

                        if action == "toggle_record":
                            record_open = not record_open
                            if not record_open:
                                record_scroll = 0

                            settings_open = False
                            settings_save_open = False
                            settings_load_open = False
                            continue

                        if action == "toggle_arrow_hint":
                            arrow_hint_enabled = not arrow_hint_enabled
                            continue

                        if action == "toggle_preview_drop":
                            preview_drop_enabled = not preview_drop_enabled
                            continue

                        if action == "toggle_preview_eat":
                            preview_eat_enabled = not preview_eat_enabled
                            continue

                        if action == "toggle_preview_fire":
                            preview_fire_enabled = not preview_fire_enabled
                            continue

                        if action == "export_record":
                            try:
                                export_record_to_file(game, record_export_filename)
                                status_message = f"已导出棋谱到 {record_export_filename}"
                                status_is_error = False
                            except Exception as e:
                                status_message = f"导出失败：{e}"
                                status_is_error = True
                            continue

                        if action == "endgame":
                            confirm_dialog = {
                                "title": "确认终局",
                                "message": "是否确认双方同意结束当前对局？\n系统将按当前局面计算胜负。",
                            }
                            confirm_action = "endgame"
                            settings_open = False
                            continue

                        if action == "resign":
                            confirm_dialog = {
                                "title": "确认投降",
                                "message": "是否确认当前行动方投降？\n确认后将直接判负。",
                            }
                            confirm_action = "resign"
                            settings_open = False
                            continue

                        if action == "quit_game":
                            open_quit_confirm()
                            settings_open = False
                            settings_save_open = False
                            settings_load_open = False
                            continue

                        continue

                handled = False
                for key, rect in system_button_rects.items():
                    if rect.collidepoint(mx, my):
                        if key == "undo":
                            try:
                                game.undo()
                                game.clear_pending_auto_action()
                                clear_transient_ui_state()
                                status_message = "已撤销上一步操作。"
                                status_is_error = False
                            except Exception as e:
                                status_message = f"撤销失败：{e}"
                                status_is_error = True
                            handled = True
                            break

                        elif key == "backtrack":
                            try:
                                if game.phase == "drop":
                                    status_message = "当前已经处于落子阶段，无法继续回退。"
                                    status_is_error = True
                                else:
                                    start_player = game.current_player
                                    stepped = 0

                                    while game.can_undo():
                                        game.undo()
                                        stepped += 1

                                        if game.phase == "drop" and game.current_player == start_player:
                                            break

                                    game.clear_pending_auto_action()
                                    clear_transient_ui_state()
                                    status_message = f"已回退 {stepped} 步，回到落子阶段。"
                                    status_is_error = False
                            except Exception as e:
                                status_message = f"回退失败：{e}"
                                status_is_error = True
                            handled = True
                            break

                        elif key == "restart":
                            game = Game()
                            clear_transient_ui_state()
                            status_message = "已重新开始对局。"
                            status_is_error = False
                            handled = True
                            break

                        elif key == "settings":
                            settings_open = True
                            handled = True
                            break

                if handled:
                    continue
                board_pos = pixel_to_board(win_mx, win_my)

                if record_open:
                    handled, new_scroll, should_close = handle_record_panel_click(
                        mx,
                        my,
                        overlay_button_rects,
                        record_scroll,
                        len(game.history),
                        6,
                    )

                    if handled:
                        record_scroll = new_scroll
                        if should_close:
                            record_open = False
                        continue

                if game.has_pending_auto_action():
                    handled, message, is_error = handle_pending_auto_action_click(game)
                    if handled:
                        status_message = message
                        status_is_error = is_error
                        continue

                if board_pos is not None:
                    x, y = board_pos
                    handled, message, is_error = handle_board_phase_click(game, legal_actions, x, y)

                    if handled:
                        status_message = message
                        status_is_error = is_error

        _unused_action_items, system_button_rects, overlay_button_rects = render_all(
            screen,
            snapshot,
            preview_board_data,
            legal_highlights,
            capturable_cells,
            hovered_eat_cells,
            cannon_highlights,
            hovered_cannon_highlights,
            hovered_cell,
            status_message,
            status_is_error,
            fonts,
            mouse_pos,
            record_open,
            game.history,
            record_scroll,
            confirm_dialog,
            settings_open,
            arrow_hint_enabled,
            preview_drop_enabled,
            preview_eat_enabled,
            preview_fire_enabled,
            app_mode,
            menu_load_open,
            settings_save_open,
            settings_load_open,
        )
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()