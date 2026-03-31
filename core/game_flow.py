#game_flow.py
from __future__ import annotations

from typing import List


def start_resolution_for_current_player_impl(self) -> None:
    from core.cannon import auto_determine_mouth, cannon_signature
    from core.record import player_name

    self.fire_cannon_pool = []
    self.pending_muzzle_cannons = []
    self.waiting_new_pool_cannons = []

    cannons = self.get_cannons_by_color(self.current_player)

    for cannon in cannons:
        if cannon.mouth is None:
            mouth = auto_determine_mouth(cannon, self.last_change_reached)
            if mouth is None:
                self.pending_muzzle_cannons.append(cannon)
                self.waiting_new_pool_cannons.append(cannon)
            else:
                cannon.mouth = mouth
                self.cannon_mouth_map[cannon_signature(cannon)] = mouth

        if cannon.mouth is not None:
            self.fire_cannon_pool.append(cannon)

    if self.pending_muzzle_cannons:
        self.phase = "muzzle"
    else:
        self.phase = "fire"

    self._record_phase_change_event()


def has_pending_muzzle_choice_impl(self) -> bool:
    return bool(self.pending_muzzle_cannons)


def all_legal_moves_impl(self, color: str) -> List[str]:
    moves: List[str] = []

    for x, y in self.board.legal_place_positions(color):
        moves.append(f"move {x} {y}   [放置]")

    for x, y in self.board.legal_upgrade_positions(color):
        piece = self.board.get(x, y)
        if piece is not None:
            moves.append(f"move {x} {y}   [升级到{piece.level + 1}级]")

    return moves


def can_player_move_impl(self, color: str) -> bool:
    return bool(self.board.legal_place_positions(color) or self.board.legal_upgrade_positions(color))


def check_game_over_at_turn_start_impl(self) -> bool:
    if self.phase != "drop":
        return False

    if self.game_over:
        return True

    if not self.can_player_move(self.current_player):
        self.finish_game(reason="no_legal_move", winner=None)
        return True

    return False


def end_turn_impl(self) -> None:
    self.current_player = self.opponent(self.current_player)
    self.turn_number += 1

    self.clear_pending_auto_action()
    self.phase = "drop"
    self.pending_muzzle_cannons = []
    self.last_new_cannons = []
    self.fire_cannon_pool = []
    self.waiting_new_pool_cannons = []
    self.last_change_reached = {}
    self.last_fire_report_lines = []


def finish_full_round_impl(self) -> None:
    next_drop_player = (
        self.opponent(self.round_drop_player)
        if self.round_drop_player is not None
        else self.opponent(self.current_player)
    )

    self.current_player = next_drop_player
    self.turn_number += 1

    self.phase = "drop"
    self.round_drop_player = None
    self.chain_pass_count = 0

    self.clear_pending_auto_action()
    self.pending_muzzle_cannons = []
    self.last_new_cannons = []
    self.fire_cannon_pool = []
    self.waiting_new_pool_cannons = []
    self.last_change_reached = {}
    self.last_fire_report_lines = []

    self._record_turn_change_event("full_round_finished")
    self._record_phase_change_event()


def advance_turn_impl(self) -> None:
    from core.record import format_cannon_for_record

    while True:
        if self.phase == "muzzle":
            return

        if self.phase == "fire":
            fireable = self.get_fireable_cannons()

            if len(fireable) >= 2:
                return

            if len(fireable) == 1:
                cannon = fireable[0]
                action = self.get_legal_fire_actions()[0]

                if self.last_new_cannons:
                    formed_text = "、".join(
                        format_cannon_for_record(c, self.cannon_record_style)
                        for c in self.last_new_cannons
                    )
                    message = (
                        f"本步形成{formed_text}\n"
                        f"当前仅有 1 门可发射炮，可点击棋盘任意位置确认发射 "
                        f"{format_cannon_for_record(cannon, self.cannon_record_style)}"
                    )
                else:
                    message = (
                        f"当前仅有 1 门可发射炮，可点击棋盘任意位置确认发射 "
                        f"{format_cannon_for_record(cannon, self.cannon_record_style)}"
                    )

                self.set_pending_auto_action(action, message)
                return

            self.phase = "eat"
            continue

        if self.phase == "eat":
            targets = self.get_capturable_targets(self.current_player)

            if len(targets) >= 2:
                return

            if len(targets) == 1:
                x, y = targets[0]
                action = self.get_legal_eat_actions()[0]
                message = f"当前仅有 1 个可吃目标，可点击棋盘任意位置确认吃掉 ({x}, {y})"

                self.set_pending_auto_action(action, message)
                return

            self.chain_pass_count += 1

            if self.chain_pass_count >= 2:
                self.add_last_action_event(
                    self._make_event(
                        "auto_action",
                        action_type="finish_full_round",
                        reason="both_sides_cannot_continue",
                    )
                )
                self.finish_full_round()
                return

            previous_player = self.current_player
            self.current_player = self.opponent(self.current_player)

            self.add_last_action_event(
                self._make_event(
                    "auto_action",
                    action_type="switch_resolution_side",
                    reason="current_side_cannot_continue",
                    from_player=previous_player,
                    to_player=self.current_player,
                    to_player_name=self.current_player,
                )
            )

            self.start_resolution_for_current_player()
            continue

        return


def calculate_score_impl(self) -> tuple[int, int]:
    red_score = self.board.piece_sum("R")
    blue_score = self.board.piece_sum("B") + 9
    return red_score, blue_score


def determine_winner_by_score_impl(self) -> str | None:
    red_score, blue_score = self.calculate_score()

    if red_score > blue_score:
        return "R"
    if blue_score > red_score:
        return "B"
    return None


def finish_game_impl(
    self,
    reason: str,
    winner: str | None = None,
) -> None:
    self.game_over = True
    self.game_over_reason = reason

    if winner is None:
        winner = self.determine_winner_by_score()

    self.winner = winner
    self.phase = "drop"
    self.clear_pending_auto_action()


def finish_by_agreement_impl(self) -> None:
    self.finish_game(reason="agreement", winner=None)


def resign_impl(self, resigning_player: str | None = None) -> None:
    if resigning_player is None:
        resigning_player = self.current_player

    winner = self.opponent(resigning_player)
    self.finish_game(reason="resign", winner=winner)