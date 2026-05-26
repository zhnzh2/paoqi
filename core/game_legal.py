#game_legal.py
from __future__ import annotations

from typing import Any


def action_label_impl(self, action: dict[str, Any]) -> str:
    action_type = action["type"]

    if action_type == "move":
        x = action["x"]
        y = action["y"]
        if action["mode"] == "place":
            return f"move {x} {y} [放置]"
        return f"move {x} {y} [升级到{action['to_level']}级]"

    if action_type == "muzzle":
        return f"cannon {action['index']} {action['direction']}"

    if action_type == "fire":
        return f"fire {action['index']}"

    if action_type == "eat":
        return f"eat {action['index']}"

    return str(action)


def action_with_label_impl(self, action: dict[str, Any]) -> dict[str, Any]:
    result = action.copy()
    result["label"] = self._action_label(action)
    return result


def action_to_command_text_impl(self, action: dict[str, Any]) -> str:
    action_type = action["type"]

    if action_type == "move":
        return f"move {action['x']} {action['y']}"

    if action_type == "muzzle":
        return f"cannon {action['index']} {action['direction']}"

    if action_type == "fire":
        return f"fire {action['index']}"

    if action_type == "eat":
        return f"eat {action['index']}"

    raise ValueError(f"未知动作类型：{action_type}")


def legal_action_command_texts_impl(self) -> list[str]:
    return [
        self.action_to_command_text(action)
        for action in self.get_legal_actions()
    ]


def get_legal_drop_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for x, y in self.board.legal_place_positions(self.current_player):
        actions.append(
            self._action_with_label(
                {
                    "type": "move",
                    "mode": "place",
                    "x": x,
                    "y": y,
                    "player": self.current_player,
                    "phase": "drop",
                }
            )
        )

    for x, y in self.board.legal_upgrade_positions(self.current_player):
        piece = self.board.get(x, y)
        if piece is None:
            continue

        actions.append(
            self._action_with_label(
                {
                    "type": "move",
                    "mode": "upgrade",
                    "x": x,
                    "y": y,
                    "to_level": piece.level + 1,
                    "player": self.current_player,
                    "phase": "drop",
                }
            )
        )

    return actions


def get_legal_muzzle_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for i, cannon in enumerate(self.pending_muzzle_cannons, start=1):
        if cannon.direction == "H":
            directions = ["left", "right"]
        else:
            directions = ["up", "down"]

        for direction in directions:
            actions.append(
                self._action_with_label(
                    {
                        "type": "muzzle",
                        "index": i,
                        "direction": direction,
                        "player": self.current_player,
                        "phase": "muzzle",
                        "cannon": self._serialize_cannon(cannon),
                    }
                )
            )

    return actions


def get_legal_fire_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for i, cannon in enumerate(self.get_fireable_cannons(), start=1):
        actions.append(
            self._action_with_label(
                {
                    "type": "fire",
                    "index": i,
                    "player": self.current_player,
                    "phase": "fire",
                    "cannon": self._serialize_cannon(cannon),
                }
            )
        )

    return actions


def get_legal_eat_actions_impl(self) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    targets = self.get_capturable_targets(self.current_player)

    for i, (x, y) in enumerate(targets, start=1):
        actions.append(
            self._action_with_label(
                {
                    "type": "eat",
                    "index": i,
                    "x": x,
                    "y": y,
                    "player": self.current_player,
                    "phase": "eat",
                    "target_piece": self._serialize_piece_at(x, y),
                }
            )
        )

    return actions


def get_legal_actions_impl(self) -> list[dict[str, Any]]:
    if self.game_over:
        return []

    if self.phase == "drop":
        return self.get_legal_drop_actions()

    if self.phase == "muzzle":
        return self.get_legal_muzzle_actions()

    if self.phase == "fire":
        return self.get_legal_fire_actions()

    if self.phase == "eat":
        return self.get_legal_eat_actions()

    return []


def get_legal_actions_snapshot_impl(self) -> dict[str, Any]:
    actions = self.get_legal_actions()
    single_action = actions[0] if len(actions) == 1 else None

    return {
        "phase": self.phase,
        "current_player": self.current_player,
        "count": len(actions),
        "has_single_action": len(actions) == 1,
        "single_action": single_action,
        "actions": actions,
    }


def get_action_api_snapshot_impl(self) -> dict[str, Any]:
    return {
        "supports_structured_actions": True,
        "supports_apply_action": True,
        "supports_try_apply_action": True,
        "supports_apply_action_with_snapshot": True,
        "supports_try_apply_action_with_snapshot": True,
        "legal_action_count": len(self.get_legal_actions()),
        "has_single_legal_action": self.has_single_legal_action(),
        "single_legal_action": self.get_single_legal_action(),
        "supports_structured_events": True,
        "supports_auto_resolution_events": True,
        "supports_state_export": True,
        "supports_state_import": True,
    }


def has_single_legal_action_impl(self) -> bool:
    return len(self.get_legal_actions()) == 1


def get_single_legal_action_impl(self) -> dict[str, Any] | None:
    actions = self.get_legal_actions()
    if len(actions) != 1:
        return None
    return actions[0]


def is_action_legal_impl(self, action: dict[str, Any]) -> bool:
    legal_actions = self.get_legal_actions()

    for legal_action in legal_actions:
        if self._actions_equal_for_execution(action, legal_action):
            return True

    return False


def actions_equal_for_execution_impl(
    self,
    action1: dict[str, Any],
    action2: dict[str, Any],
) -> bool:
    keys_by_type = {
        "move": ["type", "mode", "x", "y"],
        "muzzle": ["type", "index", "direction"],
        "fire": ["type", "index"],
        "eat": ["type", "index"],
    }

    action_type_1 = action1.get("type")
    action_type_2 = action2.get("type")

    if action_type_1 != action_type_2:
        return False

    keys = keys_by_type.get(action_type_1)
    if keys is None:
        return False

    for key in keys:
        if action1.get(key) != action2.get(key):
            return False

    return True