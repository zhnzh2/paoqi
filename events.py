#events.py
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from record import player_name

if TYPE_CHECKING:
    from game import Game


def make_event(event_type: str, **payload: Any) -> dict[str, Any]:
    event = {"type": event_type}
    event.update(payload)
    return event


def make_position_event_payload(x: int, y: int) -> dict[str, int]:
    return {"x": x, "y": y}


def make_piece_change_event(
    x: int,
    y: int,
    before_piece: dict[str, Any] | None,
    after_piece: dict[str, Any] | None,
    reason: str,
) -> dict[str, Any]:
    return make_event(
        "piece_change",
        x=x,
        y=y,
        before=before_piece,
        after=after_piece,
        reason=reason,
    )


def clear_last_action_events(game: "Game") -> None:
    game.last_action_events = []


def add_last_action_event(game: "Game", event: dict[str, Any]) -> None:
    game.last_action_events.append(event)


def get_last_action_events(game: "Game") -> list[dict[str, Any]]:
    return [event.copy() for event in game.last_action_events]


def record_phase_change_event(game: "Game") -> None:
    add_last_action_event(
        game,
        make_event(
            "phase_change",
            phase=game.phase,
            phase_name=game.phase_name(),
            current_player=game.current_player,
            current_player_name=player_name(game.current_player),
        ),
    )


def record_turn_change_event(game: "Game", reason: str) -> None:
    add_last_action_event(
        game,
        make_event(
            "turn_change",
            reason=reason,
            current_player=game.current_player,
            current_player_name=player_name(game.current_player),
            turn_number=game.turn_number,
            phase=game.phase,
            phase_name=game.phase_name(),
        ),
    )