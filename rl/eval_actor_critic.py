from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from rl.dataset import flatten_observation
from rl.env import PaoqiEnv
from rl.policy_model import ActorCriticMLP, select_action_id_from_actor_critic
from rl.rollout import sample_random_action_id


def save_json(data: Any, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_actor_critic_from_checkpoint(
    checkpoint_path: str,
    device: str = "cpu",
) -> ActorCriticMLP:
    model = ActorCriticMLP().to(device)
    state_dict = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def choose_action_id_for_actor_critic(
    model: ActorCriticMLP,
    env: PaoqiEnv,
    greedy: bool = True,
    device: str = "cpu",
) -> dict[str, Any]:
    obs = env.get_observation()
    features = flatten_observation(obs)
    action_mask = env.get_action_mask()

    result = select_action_id_from_actor_critic(
        model=model,
        features=features,
        action_mask=action_mask,
        greedy=greedy,
        device=device,
    )
    return result


def run_actor_critic_vs_random_game(
    model: ActorCriticMLP,
    model_color: str = "R",
    max_steps: int = 300,
    greedy: bool = True,
    device: str = "cpu",
) -> dict[str, Any]:
    if model_color not in ("R", "B"):
        raise ValueError(f"model_color 必须是 'R' 或 'B'，实际为 {model_color}")

    env = PaoqiEnv()
    obs, info = env.reset()

    step = 0
    action_log: list[dict[str, Any]] = []

    while step < max_steps and not env.game.is_terminal():
        current_player = info["current_player"]
        action_mask = info["action_mask"]

        if sum(action_mask) == 0:
            break

        if current_player == model_color:
            action_result = choose_action_id_for_actor_critic(
                model=model,
                env=env,
                greedy=greedy,
                device=device,
            )
            action_id = action_result["action_id"]
            state_value = float(action_result["state_value"].item())
            agent_type = "actor_critic"
        else:
            action_id = sample_random_action_id(action_mask)
            state_value = None
            agent_type = "random"

        obs, reward, done, info = env.step(action_id)

        action_log.append(
            {
                "step": step + 1,
                "player": current_player,
                "agent_type": agent_type,
                "action_id": action_id,
                "state_value": state_value,
                "reward": reward,
                "done": done,
            }
        )

        step += 1

        if done:
            break

    reached_step_limit = (not env.game.is_terminal() and step >= max_steps)

    if reached_step_limit:
        winner = env.game.determine_winner_by_score()
    else:
        winner = env.game.get_winner()

    random_color = "B" if model_color == "R" else "R"

    if winner == model_color:
        result_label = "model_win"
    elif winner == random_color:
        result_label = "random_win"
    else:
        result_label = "draw"

    return {
        "winner": winner,
        "result_label": result_label,
        "steps": step,
        "model_color": model_color,
        "random_color": random_color,
        "is_terminal": env.game.is_terminal(),
        "reached_step_limit": reached_step_limit,
        "final_board": env.render(),
        "history": env.game.history.copy(),
        "command_log": env.game.command_log.copy(),
        "action_log": action_log,
    }


def summarize_match_results(
    results: list[dict[str, Any]],
    model_color: str,
) -> dict[str, Any]:
    n_games = len(results)
    random_color = "B" if model_color == "R" else "R"

    model_win = sum(1 for r in results if r["winner"] == model_color)
    random_win = sum(1 for r in results if r["winner"] == random_color)
    draw = sum(1 for r in results if r["winner"] is None)

    avg_steps = sum(r["steps"] for r in results) / n_games if n_games > 0 else 0.0
    reached_step_limit_count = sum(1 for r in results if r["reached_step_limit"])

    return {
        "n_games": n_games,
        "model_color": model_color,
        "random_color": random_color,
        "model_win": model_win,
        "random_win": random_win,
        "draw": draw,
        "model_win_rate": model_win / n_games if n_games > 0 else 0.0,
        "random_win_rate": random_win / n_games if n_games > 0 else 0.0,
        "draw_rate": draw / n_games if n_games > 0 else 0.0,
        "avg_steps": avg_steps,
        "reached_step_limit_count": reached_step_limit_count,
        "step_limit_rate": (
            reached_step_limit_count / n_games if n_games > 0 else 0.0
        ),
        "results": results,
    }


def evaluate_actor_critic_vs_random(
    checkpoint_path: str,
    n_games: int = 20,
    model_color: str = "R",
    max_steps: int = 300,
    greedy: bool = True,
    device: str = "cpu",
) -> dict[str, Any]:
    model = load_actor_critic_from_checkpoint(
        checkpoint_path=checkpoint_path,
        device=device,
    )

    results: list[dict[str, Any]] = []

    for _ in range(n_games):
        game_result = run_actor_critic_vs_random_game(
            model=model,
            model_color=model_color,
            max_steps=max_steps,
            greedy=greedy,
            device=device,
        )
        results.append(game_result)

    summary = summarize_match_results(results, model_color=model_color)
    summary["checkpoint_path"] = checkpoint_path
    summary["greedy"] = greedy
    summary["max_steps"] = max_steps
    return summary


def evaluate_actor_critic_vs_random_balanced(
    checkpoint_path: str,
    n_games_per_color: int = 20,
    max_steps: int = 300,
    greedy: bool = True,
    device: str = "cpu",
) -> dict[str, Any]:
    red_summary = evaluate_actor_critic_vs_random(
        checkpoint_path=checkpoint_path,
        n_games=n_games_per_color,
        model_color="R",
        max_steps=max_steps,
        greedy=greedy,
        device=device,
    )

    blue_summary = evaluate_actor_critic_vs_random(
        checkpoint_path=checkpoint_path,
        n_games=n_games_per_color,
        model_color="B",
        max_steps=max_steps,
        greedy=greedy,
        device=device,
    )

    all_results = red_summary["results"] + blue_summary["results"]
    total_games = len(all_results)

    model_win = red_summary["model_win"] + blue_summary["model_win"]
    random_win = red_summary["random_win"] + blue_summary["random_win"]
    draw = red_summary["draw"] + blue_summary["draw"]
    reached_step_limit_count = (
        red_summary["reached_step_limit_count"] + blue_summary["reached_step_limit_count"]
    )
    avg_steps = (
        sum(r["steps"] for r in all_results) / total_games if total_games > 0 else 0.0
    )

    return {
        "checkpoint_path": checkpoint_path,
        "n_games_per_color": n_games_per_color,
        "total_games": total_games,
        "greedy": greedy,
        "max_steps": max_steps,
        "model_win": model_win,
        "random_win": random_win,
        "draw": draw,
        "model_win_rate": model_win / total_games if total_games > 0 else 0.0,
        "random_win_rate": random_win / total_games if total_games > 0 else 0.0,
        "draw_rate": draw / total_games if total_games > 0 else 0.0,
        "avg_steps": avg_steps,
        "reached_step_limit_count": reached_step_limit_count,
        "step_limit_rate": (
            reached_step_limit_count / total_games if total_games > 0 else 0.0
        ),
        "red_side_summary": red_summary,
        "blue_side_summary": blue_summary,
        "results": all_results,
    }