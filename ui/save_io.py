#ui/save_io.py
from __future__ import annotations

import json

from core.game import Game


def save_game_to_file(game: Game, filename: str) -> None:
    data = game.export_full_state()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game_from_file(filename: str) -> Game:
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Game.from_exported_state(data)


def export_record_to_file(game: Game, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        if game.history:
            f.write("\n".join(game.history))
        else:
            f.write("（暂无棋谱）")