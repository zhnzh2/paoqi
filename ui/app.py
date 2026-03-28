# ui/app.py

from __future__ import annotations

import json
import pygame

from core.game import Game
from ui.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from ui.controller import (
    pixel_to_board,
    find_drop_action_by_cell,
    get_legal_cell_highlights,
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
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    fonts = make_fonts()
    quit_button_rect = get_quit_button_rect()
    action_button_items: list[tuple[pygame.Rect, dict]] = []
    hover_cannon_highlights: list[dict] = []
    system_button_rects: dict[str, pygame.Rect] = {}
    quick_save_filename = "save_ui.json"
    mouse_pos: tuple[int, int] | None = None

    game = Game()
    status_message = "第一轮 UI：先实现棋盘显示和落子点击。"
    status_is_error = False

    running = True
    while running:
        snapshot = game.get_state_snapshot()
        mouse_pos = pygame.mouse.get_pos()
        legal_actions = game.get_legal_actions()

        legal_highlights = {}
        capturable_cells = get_capturable_highlights(legal_actions)
        cannon_highlights = get_fire_cannon_highlights(legal_actions)

        # 第一轮只处理落子阶段高亮
        if game.phase == "drop":
            legal_highlights = get_legal_cell_highlights(legal_actions)

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
                mx, my = event.pos
                mouse_pos = (mx, my)
                hover_cannon_highlights = []

                for rect, action in action_button_items:
                    if rect.collidepoint(mx, my):
                        cannon = action.get("cannon")
                        if isinstance(cannon, dict):
                            hover_cannon_highlights = [
                                {
                                    "type": action.get("type"),
                                    "index": action.get("index"),
                                    "direction": action.get("direction"),
                                    "cannon": cannon,
                                    "label": action.get("label", ""),
                                }
                            ]
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if quit_button_rect.collidepoint(mx, my):
                    running = False
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
                                hover_cannon_highlights = []
                            except Exception as e:
                                status_message = f"撤销失败：{e}"
                                status_is_error = True
                            handled = True
                            break

                        elif key == "restart":
                            game = Game()
                            status_message = "已重新开始对局。"
                            status_is_error = False
                            hover_cannon_highlights = []
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
                                hover_cannon_highlights = []
                            except Exception as e:
                                status_message = f"读档失败：{e}"
                                status_is_error = True
                            handled = True
                            break
                if handled:
                    continue

                # 先检查右侧动作按钮
                for rect, action in action_button_items:
                    if rect.collidepoint(mx, my):
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
                            hover_cannon_highlights = []
                        else:
                            status_message = f"操作失败：{result['message']}"
                            status_is_error = True

                        handled = True
                        break

                if handled:
                    continue

                board_pos = pixel_to_board(mx, my)

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
                                status_message = (
                                    f"操作成功：{payload.get('action_text', standardized)}\n"
                                    f"当前阶段：{phase_info.get('phase_name', game.phase_name())}"
                                )
                                status_is_error = False
                                hover_cannon_highlights = []
                            else:
                                status_message = f"操作失败：{result['message']}"
                                status_is_error = True
                    else:
                        status_message = (
                            f"当前阶段是 {game.phase_name()}。\n"
                            "请点击右侧动作按钮执行操作。"
                        )
                        status_is_error = True
                        
        action_button_items, system_button_rects = render_all(
            screen,
            snapshot,
            legal_highlights,
            capturable_cells,
            cannon_highlights,
            hover_cannon_highlights,
            status_message,
            status_is_error,
            fonts,
            mouse_pos,
        )
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()