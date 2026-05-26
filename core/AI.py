# AI.py
from __future__ import annotations

import random

from math import inf
from typing import Any

from core.game import Game

def evaluate(game: Game, perspective: str) -> float:
    if game.is_terminal():
        winner = game.get_winner()
        if winner == perspective:
            return 100000.0
        if winner is None:
            return 0.0
        return -100000.0

    opponent = game.opponent(perspective)

    my_piece_count = game.board.count_pieces(perspective)
    opp_piece_count = game.board.count_pieces(opponent)

    my_total_level = game.board.piece_sum(perspective)
    opp_total_level = game.board.piece_sum(opponent)

    my_cannon_count = len(game.get_cannons_by_color(perspective))
    opp_cannon_count = len(game.get_cannons_by_color(opponent))

    my_capture_count = len(game.get_capturable_targets(perspective))
    opp_capture_count = len(game.get_capturable_targets(opponent))

    my_high_level_count = count_high_level_pieces(game, perspective)
    opp_high_level_count = count_high_level_pieces(game, opponent)

    my_center_score = center_control_score(game, perspective)
    opp_center_score = center_control_score(game, opponent)

    score = 0.0
    score += 10.0 * (my_piece_count - opp_piece_count)
    score += 2.0 * (my_total_level - opp_total_level)
    score += 8.0 * (my_cannon_count - opp_cannon_count)
    score += 5.0 * (my_capture_count - opp_capture_count)
    score += 4.0 * (my_high_level_count - opp_high_level_count)
    score += 1.5 * (my_center_score - opp_center_score)

    return score

def action_priority(action: dict) -> int:
    action_type = action.get("type")

    if action_type == "eat":
        return 5
    if action_type == "fire":
        return 4
    if action_type == "muzzle":
        return 3
    if action_type == "move":
        mode = action.get("mode")
        if mode == "upgrade":
            return 2
        return 1

    return 0

def count_high_level_pieces(game: Game, color: str) -> int:
    count = 0
    for x in range(1, 10):
        for y in range(1, 10):
            piece = game.board.get(x, y)
            if piece is not None and piece.color == color and piece.level >= 3:
                count += 1
    return count

def center_control_score(game: Game, color: str) -> int:
    score = 0
    center_cells = [
        (4, 4), (4, 5), (4, 6),
        (5, 4), (5, 5), (5, 6),
        (6, 4), (6, 5), (6, 6),
    ]

    for x, y in center_cells:
        piece = game.board.get(x, y)
        if piece is not None and piece.color == color:
            score += piece.level

    return score

def alphabeta(
    game: Game,
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
    perspective: str,
):
    if depth == 0 or game.is_terminal():
        return evaluate(game, perspective), None

    actions = game.get_legal_actions()
    if not actions:
        return evaluate(game, perspective), None

    actions = sorted(actions, key=action_priority, reverse=True)

    best_action = None

    if maximizing:
        value = -inf
        for action in actions:
            child = game.clone()
            child.apply_action(action)

            next_maximizing = (child.current_player == perspective)

            score, _ = alphabeta(
                child,
                depth - 1,
                alpha,
                beta,
                next_maximizing,
                perspective,
            )

            if score > value:
                value = score
                best_action = action

            alpha = max(alpha, value)
            if beta <= alpha:
                break

        return value, best_action

    else:
        value = inf
        for action in actions:
            child = game.clone()
            child.apply_action(action)

            next_maximizing = (child.current_player == perspective)

            score, _ = alphabeta(
                child,
                depth - 1,
                alpha,
                beta,
                next_maximizing,
                perspective,
            )

            if score < value:
                value = score
                best_action = action

            beta = min(beta, value)
            if beta <= alpha:
                break

        return value, best_action

class AlphaBetaAgent:
    def __init__(self, color: str, depth: int = 2, verbose: bool = False, random_tiebreak: bool = True,):
        self.color = color
        self.depth = depth
        self.verbose = verbose
        self.random_tiebreak = random_tiebreak

    def choose_action(self, game: Game) -> dict[str, Any] | None:
        actions = game.get_legal_actions()
        if not actions:
            return None

        actions = sorted(actions, key=action_priority, reverse=True)

        maximizing = (game.current_player == self.color)

        best_actions = []
        if maximizing:
            best_score = -inf
        else:
            best_score = inf

        if self.verbose:
            print(
                f"\n[AI] 玩家 {self.color} 开始搜索，"
                f"当前执子：{game.current_player}，depth={self.depth}"
            )

        for action in actions:
            child = game.clone()
            child.apply_action(action)

            next_maximizing = (child.current_player == self.color)

            score, _ = alphabeta(
                game=child,
                depth=self.depth - 1,
                alpha=-inf,
                beta=inf,
                maximizing=next_maximizing,
                perspective=self.color,
            )

            if self.verbose:
                label = action.get("label", str(action))
                print(f"[AI] 候选动作：{label} -> score = {score}")

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_actions = [action]
                elif score == best_score:
                    best_actions.append(action)
            else:
                if score < best_score:
                    best_score = score
                    best_actions = [action]
                elif score == best_score:
                    best_actions.append(action)

        best_action = None
        if best_actions:
            if self.random_tiebreak:
                best_action = random.choice(best_actions)
            else:
                best_action = best_actions[0]

        if self.verbose:
            if best_action is not None:
                label = best_action.get("label", str(best_action))
                print(f"[AI] 最终选择：{label} -> score = {best_score}")
                print(f"[AI] 同分最优动作数：{len(best_actions)}")
            else:
                print("[AI] 没有选出动作")

        return best_action
    
class GreedyAgent:
    def __init__(
        self,
        color: str,
        verbose: bool = False,
        random_tiebreak: bool = True,
    ):
        self.color = color
        self.verbose = verbose
        self.random_tiebreak = random_tiebreak

    def choose_action(self, game: Game) -> dict[str, Any] | None:
        actions = game.get_legal_actions()
        if not actions:
            return None

        actions = sorted(actions, key=action_priority, reverse=True)

        best_actions = []
        best_score = -inf

        if self.verbose:
            print(f"\n[Greedy] 玩家 {self.color} 开始选步")

        for action in actions:
            child = game.clone()
            child.apply_action(action)

            score = evaluate(child, self.color)

            if self.verbose:
                label = action.get("label", str(action))
                print(f"[Greedy] 候选动作：{label} -> score = {score}")

            if score > best_score:
                best_score = score
                best_actions = [action]
            elif score == best_score:
                best_actions.append(action)

        best_action = None
        if best_actions:
            if self.random_tiebreak:
                best_action = random.choice(best_actions)
            else:
                best_action = best_actions[0]

        if self.verbose:
            if best_action is not None:
                label = best_action.get("label", str(best_action))
                print(f"[Greedy] 最终选择：{label} -> score = {best_score}")
                print(f"[Greedy] 同分最优动作数：{len(best_actions)}")
            else:
                print("[Greedy] 没有选出动作")

        return best_action

class RandomAgent:
    def __init__(self, color: str):
        self.color = color

    def choose_action(self, game: Game) -> dict[str, Any] | None:
        actions = game.get_legal_actions()
        if not actions:
            return None
        return random.choice(actions)