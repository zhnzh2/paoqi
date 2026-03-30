# ui/app.py

from __future__ import annotations

import json
import pygame

from core.game import Game
from ui.constants import WINDOW_WIDTH, WINDOW_HEIGHT, LOGICAL_WIDTH, LOGICAL_HEIGHT, FPS
from ui.controller import (
    pixel_to_board,
    window_to_logical,
    find_drop_action_by_cell,
    find_eat_action_by_cell,
    find_fire_actions_by_cell,
    find_muzzle_actions_by_endpoint,
    get_hovered_drop_highlights,
    get_hovered_eat_cells,
    get_hovered_fire_cannons,
    get_capturable_highlights,
    get_fire_cannon_highlights,
)
from ui.renderer import make_fonts, render_all, get_quit_button_rect

def save_game_to_file(game: Game, filename: str) -> None:
    data = game.export_full_state()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game_from_file(filename: str) -> Game:
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Game.from_exported_state(data)

def run_app() -> None:
    pygame.init()
    pygame.display.set_caption("炮棋（桌面版测试界面）")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), vsync=1)
    clock = pygame.time.Clock()
    fonts = make_fonts()
    quit_button_rect = get_quit_button_rect()
    system_button_rects: dict[str, pygame.Rect] = {}
    quick_save_filename = "save_ui.json"
    mouse_pos: tuple[int, int] | None = None
    hovered_cell: tuple[int, int] | None = None

    record_open = False
    record_scroll = 0
    overlay_button_rects: dict[str, pygame.Rect] = {}
    confirm_dialog: dict[str, str] | None = None
    confirm_action: str | None = None

    game = Game()
    status_message = "第一轮 UI：先实现棋盘显示和落子点击。"
    status_is_error = False

    running = True
    while running:
        if not game.game_over:
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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_u:
                    try:
                        game.undo()
                        game.log_command("undo")
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
                hovered_cell = pixel_to_board(win_mx, win_my)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                win_mx, win_my = event.pos
                mx, my = window_to_logical(win_mx, win_my)

                if quit_button_rect.collidepoint(mx, my):
                    running = False
                    continue

                if game.game_over:
                    if "game_over_restart" in overlay_button_rects and overlay_button_rects["game_over_restart"].collidepoint(mx, my):
                        game = Game()
                        status_message = "已重新开始对局。"
                        status_is_error = False
                        record_open = False
                        record_scroll = 0
                        confirm_dialog = None
                        confirm_action = None
                        continue

                    if "game_over_load" in overlay_button_rects and overlay_button_rects["game_over_load"].collidepoint(mx, my):
                        try:
                            game = load_game_from_file(quick_save_filename)
                            status_message = f"已从 {quick_save_filename} 读取存档"
                            status_is_error = False
                            record_open = False
                            record_scroll = 0
                            confirm_dialog = None
                            confirm_action = None
                        except Exception as e:
                            status_message = f"读档失败：{e}"
                            status_is_error = True
                        continue

                    if "game_over_quit" in overlay_button_rects and overlay_button_rects["game_over_quit"].collidepoint(mx, my):
                        running = False
                        continue

                    # 终局后其它按钮全部失效
                    continue

                if confirm_dialog is not None:
                    if "cancel" in overlay_button_rects and overlay_button_rects["cancel"].collidepoint(mx, my):
                        confirm_dialog = None
                        confirm_action = None
                        continue

                    if "confirm" in overlay_button_rects and overlay_button_rects["confirm"].collidepoint(mx, my):
                        if confirm_action == "endgame":
                            game.finish_by_agreement()
                            status_message = "已确认终局。"
                            status_is_error = False
                        elif confirm_action == "resign":
                            game.resign()
                            status_message = "已确认投降。"
                            status_is_error = False

                        confirm_dialog = None
                        confirm_action = None
                        continue

                handled = False
                for key, rect in system_button_rects.items():
                    if rect.collidepoint(mx, my):
                        if key == "undo":
                            try:
                                game.undo()
                                game.log_command("undo")
                                status_message = "已撤销上一步操作。"
                                status_is_error = False
                            except Exception as e:
                                status_message = f"撤销失败：{e}"
                                status_is_error = True
                            handled = True
                            break

                        elif key == "restart":
                            game = Game()
                            status_message = "已重新开始对局。"
                            status_is_error = False
                            handled = True
                            break

                        elif key == "save":
                            try:
                                save_game_to_file(game, quick_save_filename)
                                status_message = f"已保存到 {quick_save_filename}"
                                status_is_error = False
                            except Exception as e:
                                status_message = f"保存失败：{e}"
                                status_is_error = True
                            handled = True
                            break

                        elif key == "load":
                            try:
                                game = load_game_from_file(quick_save_filename)
                                status_message = f"已从 {quick_save_filename} 读取存档"
                                status_is_error = False
                            except Exception as e:
                                status_message = f"读档失败：{e}"
                                status_is_error = True
                            handled = True
                            break
                        elif key == "toggle_record":
                            record_open = not record_open
                            if not record_open:
                                record_scroll = 0
                            handled = True
                            break

                        elif key == "endgame":
                            confirm_dialog = {
                                "title": "确认终局",
                                "message": "是否确认双方同意结束当前对局？\n系统将按当前局面计算胜负。",
                            }
                            confirm_action = "endgame"
                            handled = True
                            break

                        elif key == "resign":
                            confirm_dialog = {
                                "title": "确认投降",
                                "message": "是否确认当前行动方投降？\n确认后将直接判负。",
                            }
                            confirm_action = "resign"
                            handled = True
                            break
                if handled:
                    continue
                board_pos = pixel_to_board(win_mx, win_my)

                if record_open:
                    if "record_up" in overlay_button_rects and overlay_button_rects["record_up"].collidepoint(mx, my):
                        record_scroll = max(0, record_scroll - 1)
                        continue

                    if "record_down" in overlay_button_rects and overlay_button_rects["record_down"].collidepoint(mx, my):
                        record_scroll = min(max(0, len(game.history) - 4), record_scroll + 1)
                        continue

                if game.has_pending_auto_action():
                    pending = game.pending_auto_action
                    if pending is not None:
                        result = game.try_apply_action_with_snapshot(pending)
                        if result["ok"]:
                            standardized = game.action_to_command_text(pending)
                            game.log_command(standardized)
                            status_message = f"操作成功：{standardized}"
                            status_is_error = False
                        else:
                            status_message = f"操作失败：{result['message']}"
                            status_is_error = True
                    continue

                if board_pos is not None:
                    x, y = board_pos

                    if game.phase == "drop":
                        action = find_drop_action_by_cell(legal_actions, x, y)
                        if action is None:
                            status_message = f"({x}, {y}) 不是当前合法落子位置。"
                            status_is_error = True
                        else:
                            result = game.try_apply_action_with_snapshot(action)
                            if result["ok"]:
                                standardized = game.action_to_command_text(action)
                                game.log_command(standardized)

                                payload = result.get("result", {})
                                phase_info = payload.get("after", {}).get("phase_info", {})
                                status_message = f"操作成功：{payload.get('action_text', standardized)}"
                                status_is_error = False
                            else:
                                status_message = f"操作失败：{result['message']}"
                                status_is_error = True

                    elif game.phase == "eat":
                        action = find_eat_action_by_cell(legal_actions, x, y)
                        if action is None:
                            status_message = f"({x}, {y}) 不是当前可吃目标。"
                            status_is_error = True
                        else:
                            result = game.try_apply_action_with_snapshot(action)
                            if result["ok"]:
                                standardized = game.action_to_command_text(action)
                                game.log_command(standardized)

                                payload = result.get("result", {})
                                phase_info = payload.get("after", {}).get("phase_info", {})
                                status_message = (
                                    f"操作成功：{payload.get('action_text', standardized)}\n"
                                    f"当前阶段：{phase_info.get('phase_name', game.phase_name())}"
                                )
                                status_is_error = False
                            else:
                                status_message = f"操作失败：{result['message']}"
                                status_is_error = True

                    elif game.phase == "muzzle":
                        muzzle_actions = find_muzzle_actions_by_endpoint(legal_actions, x, y)

                        if len(muzzle_actions) == 0:
                            status_message = f"({x}, {y}) 不是可选炮口端点。"
                            status_is_error = True

                        elif len(muzzle_actions) == 1:
                            action = muzzle_actions[0]
                            result = game.try_apply_action_with_snapshot(action)
                            if result["ok"]:
                                standardized = game.action_to_command_text(action)
                                game.log_command(standardized)
                                status_message = f"操作成功：{standardized}"
                                status_is_error = False
                            else:
                                status_message = f"操作失败：{result['message']}"
                                status_is_error = True

                        else:
                            status_message = f"({x}, {y}) 对应多个炮口方向，暂不自动选择。"
                            status_is_error = True

                    elif game.phase == "fire":
                        fire_actions = find_fire_actions_by_cell(legal_actions, x, y)

                        if len(fire_actions) == 0:
                            status_message = f"({x}, {y}) 不属于当前可发射炮管。"
                            status_is_error = True

                        elif len(fire_actions) == 1:
                            action = fire_actions[0]
                            result = game.try_apply_action_with_snapshot(action)
                            if result["ok"]:
                                standardized = game.action_to_command_text(action)
                                game.log_command(standardized)

                                payload = result.get("result", {})
                                phase_info = payload.get("after", {}).get("phase_info", {})
                                status_message = (
                                    f"操作成功：{payload.get('action_text', standardized)}\n"
                                    f"当前阶段：{phase_info.get('phase_name', game.phase_name())}"
                                )
                                status_is_error = False
                            else:
                                status_message = f"操作失败：{result['message']}"
                                status_is_error = True

                        else:
                            status_message = (
                                f"({x}, {y}) 同时属于 {len(fire_actions)} 门可发射炮，"
                                "暂不自动选择。"
                            )
                            status_is_error = True

                    else:
                        status_message = (
                            f"当前阶段是 {game.phase_name()}。\n"
                            "该阶段暂不支持直接点棋盘执行。"
                        )
                        status_is_error = True

        _unused_action_items, system_button_rects, overlay_button_rects = render_all(
            screen,
            snapshot,
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
        )
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()