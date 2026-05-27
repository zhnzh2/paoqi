# ui/app.py

from __future__ import annotations

from pathlib import Path

import pygame

from core.game import Game
from ui.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
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
from ui.logic_preview import compute_preview_board_data
from ui.handlers.game import handle_game_click
from ui.handlers.menu import handle_menu_click


def run_app() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    save_dir = base_dir / "saves"
    save_dir.mkdir(parents=True, exist_ok=True)

    pygame.init()
    pygame.display.set_caption("炮棋（桌面版测试界面）")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), vsync=1)
    clock = pygame.time.Clock()
    fonts = make_fonts()
    quit_button_rect = get_quit_button_rect()
    save_slot_files = {
        1: str(save_dir / "save_slot_1.json"),
        2: str(save_dir / "save_slot_2.json"),
        3: str(save_dir / "save_slot_3.json"),
    }
    record_export_filename = str(save_dir / "record_export.txt")

    mouse_pos = None
    hovered_cell = None
    overlay_button_rects = {}
    system_button_rects = {}
    confirm_dialog = None
    confirm_action = None
    record_open = False
    record_scroll = 0
    settings_open = False
    arrow_hint_enabled = True
    preview_drop_enabled = True
    preview_eat_enabled = True
    preview_fire_enabled = True
    preview_board_data = None
    app_mode = "menu"
    menu_load_open = False
    settings_save_open = False
    settings_load_open = False
    game = Game()
    status_message = ""
    status_is_error = False

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

        has_overlay = (confirm_dialog is not None or
                       (app_mode == "menu" and menu_load_open) or
                       settings_save_open or settings_load_open or
                       settings_open or record_open)
        if has_overlay:
            legal_highlights, capturable_cells, cannon_highlights = {}, [], []
            hovered_eat_cells, hovered_cannon_highlights = [], []
            hovered_cell, preview_board_data = None, None

        if game.has_pending_auto_action():
            pending = game.pending_auto_action
            if pending is not None:
                if pending.get("type") == "eat":
                    x, y = pending.get("x"), pending.get("y")
                    if isinstance(x, int) and isinstance(y, int):
                        capturable_cells = [(x, y)]
                        hovered_eat_cells = [(x, y)]
                elif pending.get("type") == "fire":
                    cannon = pending.get("cannon")
                    if isinstance(cannon, dict):
                        info = {"type": pending.get("type"), "index": pending.get("index"),
                                "direction": pending.get("direction"), "cannon": cannon,
                                "label": pending.get("label", "")}
                        cannon_highlights = [info]
                        hovered_cannon_highlights = [info]

        preview_board_data = None
        if app_mode == "game" and not has_overlay:
            preview_board_data = compute_preview_board_data(
                game, legal_actions, hovered_cell,
                preview_drop_enabled, preview_eat_enabled, preview_fire_enabled,
            )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if app_mode == "menu":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = window_to_logical(*event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = window_to_logical(*event.pos)
                    res = handle_menu_click(mx, my, overlay_button_rects,
                                            confirm_dialog, confirm_action,
                                            menu_load_open, save_slot_files)
                    running = res.get("running", running)
                    if "enter_game" in res:
                        game, status_message = res["enter_game"]
                        app_mode = "game"
                        menu_load_open = False
                        settings_open = settings_save_open = settings_load_open = False
                        record_open = False; record_scroll = 0
                        hovered_cell = None; preview_board_data = None
                        confirm_dialog = None; confirm_action = None
                        status_is_error = False
                    confirm_dialog = res.get("confirm_dialog", confirm_dialog)
                    confirm_action = res.get("confirm_action", confirm_action)
                    if "menu_load_open" in res:
                        menu_load_open = res["menu_load_open"]
                    if "status_message" in res:
                        status_message = res["status_message"]
                        status_is_error = res.get("status_is_error", False)
                continue

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_u:
                    try:
                        game.undo()
                        hovered_cell = None; confirm_dialog = None
                        confirm_action = None; record_open = False
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
                mouse_pos = window_to_logical(*event.pos)
                has_overlay2 = (confirm_dialog is not None or
                                (app_mode == "menu" and menu_load_open) or
                                settings_save_open or settings_load_open or
                                settings_open or record_open)
                hovered_cell = None if has_overlay2 else pixel_to_board(*event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = window_to_logical(*event.pos)
                res = handle_game_click(
                    mx, my, *event.pos, game, overlay_button_rects, system_button_rects,
                    quit_button_rect, confirm_dialog, confirm_action,
                    settings_open, settings_save_open, settings_load_open,
                    record_open, record_scroll, record_export_filename, save_slot_files,
                    arrow_hint_enabled, preview_drop_enabled, preview_eat_enabled, preview_fire_enabled,
                    app_mode, menu_load_open,
                )
                running = res.get("running", running)
                if "enter_game" in res:
                    game, status_message = res["enter_game"]
                    app_mode = "game"
                    menu_load_open = False
                    settings_open = settings_save_open = settings_load_open = False
                    record_open = False; record_scroll = 0
                    hovered_cell = None; preview_board_data = None
                    confirm_dialog = None; confirm_action = None
                    status_is_error = False
                if "confirm_dialog" in res:
                    confirm_dialog = res["confirm_dialog"]
                if "confirm_action" in res:
                    confirm_action = res["confirm_action"]
                if "settings_open" in res:
                    settings_open = res["settings_open"]
                if "settings_save_open" in res:
                    settings_save_open = res["settings_save_open"]
                if "settings_load_open" in res:
                    settings_load_open = res["settings_load_open"]
                if "record_open" in res:
                    record_open = res["record_open"]
                if "record_scroll" in res:
                    record_scroll = res["record_scroll"]
                if "arrow_hint_enabled" in res:
                    arrow_hint_enabled = res["arrow_hint_enabled"]
                if "preview_drop_enabled" in res:
                    preview_drop_enabled = res["preview_drop_enabled"]
                if "preview_eat_enabled" in res:
                    preview_eat_enabled = res["preview_eat_enabled"]
                if "preview_fire_enabled" in res:
                    preview_fire_enabled = res["preview_fire_enabled"]
                if "app_mode" in res:
                    app_mode = res["app_mode"]
                if "menu_load_open" in res:
                    menu_load_open = res["menu_load_open"]
                if "status_message" in res:
                    status_message = res["status_message"]
                    status_is_error = res.get("status_is_error", False)
                if "hovered_cell" in res:
                    hovered_cell = res["hovered_cell"]
                if "clear_transient" in res:
                    hovered_cell = None; preview_board_data = None
                    confirm_dialog = None; confirm_action = None
                    record_open = False
                if "reset_ui" in res:
                    menu_load_open = False
                    settings_open = settings_save_open = settings_load_open = False
                    record_open = False; record_scroll = 0
                    hovered_cell = None; preview_board_data = None
                    confirm_dialog = None; confirm_action = None
                if "game_replaced" in res:
                    game = res["game_replaced"]

        action_items, system_button_rects, overlay_button_rects = render_all(
            screen, snapshot, preview_board_data,
            legal_highlights, capturable_cells, hovered_eat_cells,
            cannon_highlights, hovered_cannon_highlights,
            hovered_cell, status_message, status_is_error,
            fonts, mouse_pos, record_open, game.history, record_scroll,
            confirm_dialog, settings_open,
            arrow_hint_enabled, preview_drop_enabled, preview_eat_enabled, preview_fire_enabled,
            app_mode, menu_load_open, settings_save_open, settings_load_open,
        )
        pygame.display.flip()
        clock.tick(FPS)
