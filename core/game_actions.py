#game_actions.py
from __future__ import annotations

from typing import Any


def apply_move_action_impl(self, action: dict[str, Any]) -> None:
    x = action["x"]
    y = action["y"]
    self.apply_move_at(x, y)


def apply_move_at_impl(self, x: int, y: int) -> None:
    from core.cannon import detect_new_cannons

    if self.phase != "drop":
        raise ValueError("当前阶段不是落子阶段，无法执行该操作。")

    if not self.board.in_bounds(x, y):
        raise ValueError("坐标越界。")

    before_piece = self._serialize_piece_at(x, y)

    self.push_undo_snapshot()
    self.clear_last_change_reached()
    self.clear_last_action_events()

    self.round_drop_player = self.current_player
    self.chain_pass_count = 0

    before_cannons = self.get_cannons_by_color(self.current_player)
    self.apply_move(x, y)
    after_piece = self._serialize_piece_at(x, y)
    after_cannons = self.get_cannons_by_color(self.current_player)

    move_reason = "place" if before_piece is None else "upgrade"
    self.add_last_action_event(
        self._make_piece_change_event(
            x=x,
            y=y,
            before_piece=before_piece,
            after_piece=after_piece,
            reason=move_reason,
        )
    )

    self.last_new_cannons = detect_new_cannons(before_cannons, after_cannons)
    self.assign_muzzles_for_new_cannons()

    for cannon in self.last_new_cannons:
        self.add_last_action_event(
            self._make_event(
                "new_cannon",
                cannon=self._serialize_cannon(cannon),
            )
        )

    self.waiting_new_pool_cannons = self.last_new_cannons.copy()

    if self.pending_muzzle_cannons:
        self.phase = "muzzle"
        self._record_phase_change_event()
    else:
        self.add_waiting_new_cannons_to_pool()
        self.phase = "fire"
        self._record_phase_change_event()

    self.advance_turn()


def apply_muzzle_choice_impl(self, index: int, direction: str) -> None:
    self.set_cannon_mouth(index, direction)


def apply_fire_choice_impl(self, index: int) -> None:
    self.fire_cannon_by_index(index)


def apply_eat_choice_impl(self, index: int) -> None:
    self.eat_target_by_index(index)


def apply_muzzle_action_impl(self, action: dict[str, Any]) -> None:
    index = action["index"]
    direction = action["direction"]
    self.apply_muzzle_choice(index, direction)


def apply_fire_action_impl(self, action: dict[str, Any]) -> None:
    index = action["index"]
    self.apply_fire_choice(index)


def apply_eat_action_impl(self, action: dict[str, Any]) -> None:
    index = action["index"]
    self.apply_eat_choice(index)


def dispatch_action_impl(self, action: dict[str, Any]) -> None:
    action_type = action["type"]

    if action_type == "move":
        self._apply_move_action(action)
        return

    if action_type == "muzzle":
        self._apply_muzzle_action(action)
        return

    if action_type == "fire":
        self._apply_fire_action(action)
        return

    if action_type == "eat":
        self._apply_eat_action(action)
        return

    raise ValueError(f"未知动作类型：{action_type}")


def apply_action_impl(self, action: dict[str, Any]) -> None:
    if self.game_over:
        raise ValueError("游戏已结束，不能继续操作。")

    if not isinstance(action, dict):
        raise ValueError("action 必须是字典。")

    action_type = action.get("type")
    if action_type is None:
        raise ValueError("action 缺少 type 字段。")

    if not self.is_action_legal(action):
        raise ValueError(f"非法动作：{action}")

    self.clear_pending_auto_action()
    self._dispatch_action(action)


def try_apply_action_impl(self, action: dict[str, Any]) -> tuple[bool, str]:
    try:
        self.apply_action(action)
        return True, "ok"
    except Exception as e:
        return False, str(e)


def apply_action_with_snapshot_impl(
    self,
    action: dict[str, Any],
) -> dict[str, Any]:
    before = self.get_state_snapshot()
    self.apply_action(action)
    after = self.get_state_snapshot()

    return {
        "action": action,
        "action_text": self.action_to_command_text(action),
        "events": self.get_last_action_events(),
        "auto_action_messages": self.auto_action_messages.copy(),
        "before": before,
        "after": after,
    }


def try_apply_action_with_snapshot_impl(
    self,
    action: dict[str, Any],
) -> dict[str, Any]:
    try:
        result = self.apply_action_with_snapshot(action)
        return {
            "ok": True,
            "message": "ok",
            "result": result,
        }
    except Exception as e:
        return {
            "ok": False,
            "message": str(e),
            "result": None,
        }


def apply_single_legal_action_impl(self) -> dict[str, Any]:
    action = self.get_single_legal_action()
    if action is None:
        raise ValueError("当前不是唯一合法动作，无法自动执行。")

    self.apply_action(action)
    return action