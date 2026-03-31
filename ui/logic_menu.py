#ui/logic_menu.py
from __future__ import annotations

from core.game import Game
from ui.save_io import load_game_from_file


def make_quit_confirm_dialog() -> dict[str, str]:
    return {
        "title": "确认退出",
        "message": "是否确认退出游戏？",
    }


def start_new_game_session() -> tuple[Game, str]:
    return Game(), "已开始新对局。"


def load_game_from_slot(
    save_slot_files: dict[int, str],
    slot: int,
) -> tuple[Game | None, str, bool]:
    try:
        game = load_game_from_file(save_slot_files[slot])
        return game, f"已从槽位 {slot} 载入对局。", False
    except Exception as e:
        return None, f"读档失败：{e}", True