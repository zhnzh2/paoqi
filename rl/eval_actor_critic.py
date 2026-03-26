#eval_actor_critic
from __future__ import annotations

from typing import Any

import torch

from rl.dataset import flatten_observation
from rl.env import PaoqiEnv
from rl.policy_model import ActorCriticMLP, select_action_id_from_actor_critic
from rl.rollout import sample_random_action_id


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

    return {
        "winner": winner,
        "steps": step,
        "model_color": model_color,
        "is_terminal": env.game.is_terminal(),
        "reached_step_limit": reached_step_limit,
        "final_board": env.render(),
        "action_log": action_log,
    }


def evaluate_actor_critic_vs_random(
    checkpoint_path: str,
    n_games: int = 10,
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
    model_win = 0
    random_win = 0
    draw = 0

    random_color = "B" if model_color == "R" else "R"

    for _ in range(n_games):
        game_result = run_actor_critic_vs_random_game(
            model=model,
            model_color=model_color,
            max_steps=max_steps,
            greedy=greedy,
            device=device,
        )
        results.append(game_result)

        winner = game_result["winner"]

        if winner == model_color:
            model_win += 1
        elif winner == random_color:
            random_win += 1
        else:
            draw += 1

    return {
        "n_games": n_games,
        "model_color": model_color,
        "random_color": random_color,
        "model_win": model_win,
        "random_win": random_win,
        "draw": draw,
        "results": results,
    }