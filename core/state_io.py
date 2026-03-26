#state_io.py
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from core.cannon import cannon_signature
from core.models import Cannon, Piece
from core.record import format_cannon_for_record, player_name

if TYPE_CHECKING:
    from core.game import Game


def phase_code(game: "Game") -> str:
    return game.phase


def winner_code(game: "Game") -> str | None:
    return game.winner


def serialize_piece_at(game: "Game", x: int, y: int) -> dict[str, Any] | None:
    piece = game.board.get(x, y)
    if piece is None:
        return None

    return {
        "color": piece.color,
        "level": piece.level,
        "short": piece.short(),
    }


def serialize_position(pos: tuple[int, int]) -> dict[str, int]:
    x, y = pos
    return {
        "x": x,
        "y": y,
    }


def serialize_cannon(game: "Game", cannon: Cannon) -> dict[str, Any]:
    return {
        "color": cannon.color,
        "level": cannon.level,
        "length": cannon.length,
        "direction": cannon.direction,
        "mouth": cannon.mouth,
        "positions": [
            {"x": x, "y": y}
            for x, y in cannon.positions
        ],
        "signature": list(cannon_signature(cannon)),
        "short": cannon.short(),
        "record_text": format_cannon_for_record(cannon, game.cannon_record_style),
    }


def get_board_snapshot(game: "Game") -> list[list[dict[str, Any] | None]]:
    rows: list[list[dict[str, Any] | None]] = []

    for y in range(1, game.board.SIZE + 1):
        row: list[dict[str, Any] | None] = []

        for x in range(1, game.board.SIZE + 1):
            row.append(serialize_piece_at(game, x, y))

        rows.append(row)

    return rows


def get_cannon_snapshot(game: "Game", cannons: list[Cannon]) -> list[dict[str, Any]]:
    return [serialize_cannon(game, cannon) for cannon in cannons]


def get_all_cannons_snapshot(game: "Game") -> dict[str, list[dict[str, Any]]]:
    red_cannons = game.get_cannons_by_color("R")
    blue_cannons = game.get_cannons_by_color("B")

    return {
        "R": get_cannon_snapshot(game, red_cannons),
        "B": get_cannon_snapshot(game, blue_cannons),
    }


def get_phase_snapshot(game: "Game") -> dict[str, Any]:
    return {
        "phase": phase_code(game),
        "phase_name": game.phase_name(),
        "current_player": game.current_player,
        "current_player_name": player_name(game.current_player),
        "turn_number": game.turn_number,
        "round_drop_player": game.round_drop_player,
        "chain_pass_count": game.chain_pass_count,
        "has_pending_muzzle_choice": game.has_pending_muzzle_choice(),
        "game_over": game.game_over,
        "winner": winner_code(game),
    }


def get_interaction_snapshot(game: "Game") -> dict[str, Any]:
    fireable = game.get_fireable_cannons()
    capturable = game.get_capturable_targets(game.current_player)

    return {
        "last_new_cannons": get_cannon_snapshot(game, game.last_new_cannons),
        "pending_muzzle_cannons": get_cannon_snapshot(game, game.pending_muzzle_cannons),
        "fire_cannon_pool": get_cannon_snapshot(game, game.fire_cannon_pool),
        "fireable_cannons": get_cannon_snapshot(game, fireable),
        "capturable_targets": [
            {
                "x": x,
                "y": y,
                "piece": serialize_piece_at(game, x, y),
            }
            for x, y in capturable
        ],
        "last_change_reached": [
            {
                "x": x,
                "y": y,
                "color": color,
                "level": level,
            }
            for (x, y), (color, level) in game.last_change_reached.items()
        ],
    }


def get_log_snapshot(game: "Game") -> dict[str, Any]:
    return {
        "history": game.history.copy(),
        "debug_log": game.debug_log.copy(),
        "command_log": game.command_log.copy(),
        "last_fire_report_lines": game.last_fire_report_lines.copy(),
        "auto_action_messages": game.auto_action_messages.copy(),
        "last_action_events": game.get_last_action_events(),
    }


def get_drop_legal_snapshot(game: "Game") -> dict[str, Any]:
    place_positions = game.board.legal_place_positions(game.current_player)
    upgrade_positions = game.board.legal_upgrade_positions(game.current_player)

    return {
        "place_positions": [
            {"x": x, "y": y}
            for x, y in place_positions
        ],
        "upgrade_positions": [
            {
                "x": x,
                "y": y,
                "to_level": game.board.get(x, y).level + 1,
            }
            for x, y in upgrade_positions
            if game.board.get(x, y) is not None
        ],
        "all_legal_moves_text": game.all_legal_moves(game.current_player),
    }


def get_state_snapshot(game: "Game") -> dict[str, Any]:
    red_score, blue_score = game.calculate_score()

    return {
        "phase_info": get_phase_snapshot(game),
        "board": get_board_snapshot(game),
        "cannons": get_all_cannons_snapshot(game),
        "interaction": get_interaction_snapshot(game),
        "drop_legal": get_drop_legal_snapshot(game),
        "legal_actions": game.get_legal_actions_snapshot(),
        "logs": get_log_snapshot(game),
        "score": {
            "R": red_score,
            "B": blue_score,
        },
        "cannon_record_style": game.cannon_record_style,
        "action_api": game.get_action_api_snapshot(),
    }


def export_board_state(game: "Game") -> list[list[dict[str, Any] | None]]:
    return get_board_snapshot(game)


def export_cannon_list(game: "Game", cannons: list[Cannon]) -> list[dict[str, Any]]:
    return [serialize_cannon(game, cannon) for cannon in cannons]


def export_full_state(game: "Game") -> dict[str, Any]:
    return {
        "board": export_board_state(game),
        "phase": game.phase,
        "current_player": game.current_player,
        "turn_number": game.turn_number,
        "round_drop_player": game.round_drop_player,
        "chain_pass_count": game.chain_pass_count,
        "game_over": game.game_over,
        "winner": game.winner,
        "cannon_record_style": game.cannon_record_style,
        "last_new_cannons": export_cannon_list(game, game.last_new_cannons),
        "pending_muzzle_cannons": export_cannon_list(game, game.pending_muzzle_cannons),
        "waiting_new_pool_cannons": export_cannon_list(game, game.waiting_new_pool_cannons),
        "fire_cannon_pool": export_cannon_list(game, game.fire_cannon_pool),
        "cannon_mouth_map": [
            {
                "signature": list(sig),
                "mouth": mouth,
            }
            for sig, mouth in game.cannon_mouth_map.items()
        ],
        "last_change_reached": [
            {
                "x": x,
                "y": y,
                "color": color,
                "level": level,
            }
            for (x, y), (color, level) in game.last_change_reached.items()
        ],
        "history": game.history.copy(),
        "debug_log": game.debug_log.copy(),
        "command_log": game.command_log.copy(),
        "last_fire_report_lines": game.last_fire_report_lines.copy(),
        "auto_action_messages": game.auto_action_messages.copy(),
        "last_action_events": game.get_last_action_events(),
    }


def deserialize_piece_data(data: dict[str, Any] | None) -> Piece | None:
    if data is None:
        return None
    return Piece(data["color"], data["level"])


def deserialize_cannon_data(data: dict[str, Any]) -> Cannon:
    return Cannon(
        color=data["color"],
        level=data["level"],
        positions=tuple((item["x"], item["y"]) for item in data["positions"]),
        direction=data["direction"],
        mouth=data["mouth"],
    )


def import_full_state(game: "Game", data: dict[str, Any]) -> None:
    for y, row in enumerate(data["board"], start=1):
        for x, cell in enumerate(row, start=1):
            game.board.set(x, y, deserialize_piece_data(cell))

    game.phase = data["phase"]
    game.current_player = data["current_player"]
    game.turn_number = data["turn_number"]
    game.round_drop_player = data["round_drop_player"]
    game.chain_pass_count = data["chain_pass_count"]
    game.game_over = data["game_over"]
    game.winner = data["winner"]
    game.cannon_record_style = data["cannon_record_style"]

    game.last_new_cannons = [
        deserialize_cannon_data(item)
        for item in data["last_new_cannons"]
    ]
    game.pending_muzzle_cannons = [
        deserialize_cannon_data(item)
        for item in data["pending_muzzle_cannons"]
    ]
    game.waiting_new_pool_cannons = [
        deserialize_cannon_data(item)
        for item in data["waiting_new_pool_cannons"]
    ]
    game.fire_cannon_pool = [
        deserialize_cannon_data(item)
        for item in data["fire_cannon_pool"]
    ]

    game.cannon_mouth_map = {}
    for item in data["cannon_mouth_map"]:
        sig = item["signature"]
        restored_sig = (
            sig[0],
            sig[1],
            tuple(tuple(pos) for pos in sig[2]),
            sig[3],
        )
        game.cannon_mouth_map[restored_sig] = item["mouth"]

    game.last_change_reached = {
        (item["x"], item["y"]): (item["color"], item["level"])
        for item in data["last_change_reached"]
    }

    game.history = data["history"].copy()
    game.debug_log = data["debug_log"].copy()
    game.command_log = data["command_log"].copy()
    game.last_fire_report_lines = data["last_fire_report_lines"].copy()
    game.auto_action_messages = data["auto_action_messages"].copy()
    game.last_action_events = [event.copy() for event in data["last_action_events"]]

    game.undo_stack = []


def from_exported_state(data: dict[str, Any]) -> "Game":
    from core.game import Game

    game = Game()
    import_full_state(game, data)
    return game


def export_import_roundtrip_snapshot(game: "Game") -> dict[str, Any]:
    data = export_full_state(game)
    clone = from_exported_state(data)
    return get_state_snapshot(clone)

