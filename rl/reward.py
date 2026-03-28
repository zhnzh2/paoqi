from __future__ import annotations

from core.game import Game


CENTER_POSITIONS = {
    (4, 4), (5, 4), (6, 4),
    (4, 5), (5, 5), (6, 5),
    (4, 6), (5, 6), (6, 6),
}


NEW_CANNON_REWARD = 0.05
FIRE_REWARD = 0.08
CAPTURE_REWARD = 0.12
CENTER_PLACE_REWARD = 0.03
CENTER_CONTROL_SCALE = 0.01


def get_terminal_reward(game: Game, perspective: str) -> float:
    winner = game.get_winner()

    if winner is None and game.is_terminal():
        winner = game.determine_winner_by_score()

    if winner == perspective:
        return 1.0

    if winner is None:
        return 0.0

    return -1.0


def center_control_score(game: Game, perspective: str) -> int:
    opponent = "B" if perspective == "R" else "R"
    score = 0

    for x, y in CENTER_POSITIONS:
        piece = game.board.get(x, y)
        if piece is None:
            continue

        if piece.color == perspective:
            score += piece.level
        elif piece.color == opponent:
            score -= piece.level

    return score


def get_event_reward(game: Game, acting_player: str) -> float:
    reward = 0.0
    events = game.get_last_action_events()

    if not events:
        return 0.0

    # 1. 成炮奖励
    new_cannon_count = 0
    for event in events:
        if event.get("type") == "new_cannon":
            cannon = event.get("cannon")
            if cannon is not None and cannon.get("color") == acting_player:
                new_cannon_count += 1

    reward += NEW_CANNON_REWARD * new_cannon_count

    # 2. 打炮奖励
    # 当前代码里没有显式 "fire" 事件，但打炮会产生 front_attack / body_upgrade 的 piece_change
    fire_related_change_count = 0
    for event in events:
        if event.get("type") != "piece_change":
            continue

        reason = event.get("reason")
        if reason in {"front_attack", "body_upgrade"}:
            fire_related_change_count += 1

    if fire_related_change_count > 0:
        reward += FIRE_REWARD

    # 3. 吃子奖励
    capture_count = 0
    for event in events:
        if event.get("type") == "capture" and event.get("player") == acting_player:
            capture_count += 1

    reward += CAPTURE_REWARD * capture_count

    # 4. 中心落子 / 中心夺子奖励
    for event in events:
        if event.get("type") != "piece_change":
            continue

        x = event.get("x")
        y = event.get("y")
        if (x, y) not in CENTER_POSITIONS:
            continue

        after_piece = event.get("after")
        if after_piece is None:
            continue

        if after_piece.get("color") != acting_player:
            continue

        reason = event.get("reason")
        if reason in {"place", "upgrade", "capture"}:
            reward += CENTER_PLACE_REWARD

    return reward


def get_center_control_reward(game: Game, acting_player: str) -> float:
    score = center_control_score(game, acting_player)
    return CENTER_CONTROL_SCALE * score


def get_step_reward(game: Game, acting_player: str) -> float:
    reward = 0.0

    reward += get_event_reward(game, acting_player)
    reward += get_center_control_reward(game, acting_player)

    if game.is_terminal():
        reward += get_terminal_reward(game, acting_player)

    return reward