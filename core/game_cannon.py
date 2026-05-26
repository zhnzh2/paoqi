#game_cannon.py
from __future__ import annotations

from typing import List


def remove_contained_old_cannons_impl(self, new_cannon) -> None:
    from core.cannon import cannon_contains

    remaining = []

    for old_cannon in self.fire_cannon_pool:
        if cannon_contains(new_cannon, old_cannon):
            self.debug(
                f"炮管集合更新: 新炮 {new_cannon.positions} 包含旧炮 {old_cannon.positions}，旧炮移出集合"
            )
        else:
            remaining.append(old_cannon)

    self.fire_cannon_pool = remaining


def get_all_cannons_impl(self) -> list:
    from core.cannon import find_all_cannons

    cannons = find_all_cannons(self.board)

    for cannon in cannons:
        self._apply_saved_mouth_to_cannon(cannon)

    return cannons


def apply_saved_mouth_to_cannon_impl(self, cannon):
    from core.cannon import cannon_signature

    sig = cannon_signature(cannon)

    if sig in self.cannon_mouth_map:
        cannon.mouth = self.cannon_mouth_map[sig]
        return cannon

    for pending in self.pending_muzzle_cannons:
        if cannon_signature(pending) == sig and pending.mouth is not None:
            cannon.mouth = pending.mouth
            return cannon

    return cannon


def initialize_fire_cannon_pool_impl(self) -> None:
    self.fire_cannon_pool = []

    for cannon in self.get_cannons_by_color(self.current_player):
        if cannon.mouth is not None:
            self.fire_cannon_pool.append(cannon)


def get_cannons_by_color_impl(self, color: str) -> list:
    return [c for c in self.get_all_cannons() if c.color == color]


def assign_muzzles_for_new_cannons_impl(self) -> None:
    from core.cannon import auto_determine_mouth, cannon_signature
    from core.record import player_name

    self.pending_muzzle_cannons = []
    auto_resolved_cannons = []

    for cannon in self.last_new_cannons:
        mouth = auto_determine_mouth(cannon, self.last_change_reached)

        if mouth is None:
            self.pending_muzzle_cannons.append(cannon)
        else:
            cannon.mouth = mouth
            self.cannon_mouth_map[cannon_signature(cannon)] = mouth
            auto_resolved_cannons.append(cannon)

            self.debug(
                f"{player_name(cannon.color)}: 新炮 {cannon.positions} 自动判定炮口为 {mouth}"
            )

    self.record_new_cannons(auto_resolved_cannons)


def add_waiting_new_cannons_to_pool_impl(self) -> None:
    from core.cannon import cannon_signature

    if not self.waiting_new_pool_cannons:
        return

    for cannon in self.waiting_new_pool_cannons:
        self._apply_saved_mouth_to_cannon(cannon)

        self.remove_contained_old_cannons(cannon)

        sig = cannon_signature(cannon)
        exists = any(cannon_signature(old) == sig for old in self.fire_cannon_pool)

        if not exists:
            self.fire_cannon_pool.append(cannon)
            self.debug(
                f"炮管集合更新: 新炮 {cannon.positions} 加入当前炮管集合"
            )

    self.waiting_new_pool_cannons = []


def set_cannon_mouth_impl(self, index: int, direction_text: str) -> None:
    from core.cannon import cannon_signature
    from core.record import player_name

    if not (1 <= index <= len(self.pending_muzzle_cannons)):
        raise ValueError("新炮编号无效。")

    cannon = self.pending_muzzle_cannons[index - 1]
    text = direction_text.lower()

    if cannon.direction == "H":
        if text == "left":
            mouth = "L"
        elif text == "right":
            mouth = "R"
        else:
            raise ValueError("横向炮只能选择 left 或 right。")
    else:
        if text == "up":
            mouth = "U"
        elif text == "down":
            mouth = "D"
        else:
            raise ValueError("纵向炮只能选择 up 或 down。")

    self.push_undo_snapshot()
    self.clear_last_action_events()
    cannon.mouth = mouth
    self.cannon_mouth_map[cannon_signature(cannon)] = mouth
    self.add_last_action_event(
        self._make_event(
            "muzzle_set",
            index=index,
            direction=direction_text.lower(),
            cannon=self._serialize_cannon(cannon),
        )
    )

    for new_cannon in self.last_new_cannons:
        if cannon_signature(new_cannon) == cannon_signature(cannon):
            new_cannon.mouth = mouth

    self.debug(
        f"{player_name(cannon.color)}: 为新炮 {cannon.positions} 指定炮口方向 {direction_text}"
    )

    self.record_new_cannons(
        [cannon],
        manual_signature_to_mouth={cannon_signature(cannon): mouth},
    )
    if self.all_pending_muzzles_set():
        self.add_waiting_new_cannons_to_pool()
        self.clear_pending_muzzles()
        self.phase = "fire"
        self._record_phase_change_event()
        self.advance_turn()


def all_pending_muzzles_set_impl(self) -> bool:
    return all(c.mouth is not None for c in self.pending_muzzle_cannons)


def clear_pending_muzzles_impl(self) -> None:
    self.pending_muzzle_cannons = []


def get_phase_relevant_cannons_impl(self) -> list:
    return self.get_cannons_by_color(self.current_player)


def get_fireable_cannons_impl(self) -> list:
    return self.fire_cannon_pool.copy()