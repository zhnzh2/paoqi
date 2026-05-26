from __future__ import annotations

from typing import Any

from core.game import Game


def build_game_payload(game: Game) -> dict[str, Any]:
    return {
        "snapshot": game.get_state_snapshot(),
        "legal_actions": game.get_legal_actions(),
        "legal_actions_snapshot": game.get_legal_actions_snapshot(),
        "has_pending_auto_action": game.has_pending_auto_action(),
        "pending_auto_action": game.pending_auto_action,
        "auto_action_messages": list(game.auto_action_messages),
        "game_over": game.game_over,
        "game_over_reason": game.game_over_reason,
        "winner": game.winner,
        "history": list(game.history),
        "turn_number": game.turn_number,
        "current_player": game.current_player,
        "phase": game.phase,
    }


def build_ok_response(
    game: Game,
    message: str = "ok",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = {
        "ok": True,
        "message": message,
        "data": build_game_payload(game),
    }
    if extra:
        data.update(extra)
    return data


def build_error_response(message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "message": message,
        "data": None,
    }