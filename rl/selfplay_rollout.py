#selfplay_rollout.py
from __future__ import annotations

from typing import Any

import torch

from rl.dataset import flatten_observation
from rl.env import PaoqiEnv
from rl.policy_model import ActorCriticMLP, apply_action_mask_to_logits
from rl.rollout import sample_random_action_id


def outcome_for_player(winner: str | None, player: str) -> float:
    if winner is None:
        return 0.0

    if winner == player:
        return 1.0

    return -1.0


def sample_action_from_actor_critic_for_selfplay(
    model: ActorCriticMLP,
    features: list[int],
    action_mask: list[int],
    device: str = "cpu",
    greedy: bool = False,
) -> dict[str, Any]:
    x = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
    mask_tensor = torch.tensor(action_mask, dtype=torch.float32, device=device).unsqueeze(0)

    output = model(x)
    policy_logits = output["policy_logits"]
    state_value = output["state_value"]

    masked_logits = apply_action_mask_to_logits(policy_logits, mask_tensor)
    dist = torch.distributions.Categorical(logits=masked_logits)

    if greedy:
        action_tensor = torch.argmax(masked_logits, dim=1)
    else:
        action_tensor = dist.sample()

    log_prob = dist.log_prob(action_tensor)
    entropy = dist.entropy()

    return {
        "action_id": int(action_tensor.item()),
        "log_prob": float(log_prob.item()),
        "entropy": float(entropy.item()),
        "value": float(state_value.item()),
        "policy_logits": policy_logits.detach().cpu(),
        "masked_logits": masked_logits.detach().cpu(),
    }


def collect_selfplay_episode(
    red_model: ActorCriticMLP | None,
    blue_model: ActorCriticMLP | None = None,
    max_steps: int = 300,
    device: str = "cpu",
    greedy: bool = False,
) -> dict[str, Any]:
    if blue_model is None:
        blue_model = red_model

    env = PaoqiEnv()
    obs, info = env.reset()

    trajectory: list[dict[str, Any]] = []
    step = 0

    while step < max_steps and not env.game.is_terminal():
        action_mask = info["action_mask"]

        if sum(action_mask) == 0:
            break

        acting_player = info["current_player"]
        phase_before = info["phase"]
        features_before = flatten_observation(obs)

        current_model = red_model if acting_player == "R" else blue_model

        if current_model is None:
            action_id = sample_random_action_id(action_mask)
            action_result = {
                "log_prob": None,
                "entropy": None,
                "value": None,
            }
            agent_type = "random"
        else:
            action_result = sample_action_from_actor_critic_for_selfplay(
                model=current_model,
                features=features_before,
                action_mask=action_mask,
                device=device,
                greedy=greedy,
            )
            action_id = action_result["action_id"]
            agent_type = "actor_critic"

        next_obs, reward, done, next_info = env.step(action_id)

        trajectory.append(
            {
                "step": step + 1,
                "acting_player": acting_player,
                "phase_before": phase_before,
                "features_before": features_before,
                "action_mask": action_mask.copy(),
                "action_id": action_id,
                "log_prob": action_result["log_prob"],
                "entropy": action_result["entropy"],
                "value": action_result["value"],
                "reward": reward,
                "done": done,
                "agent_type": agent_type,
            }
        )

        obs = next_obs
        info = next_info
        step += 1

        if done:
            break

    reached_step_limit = (not env.game.is_terminal() and step >= max_steps)

    if reached_step_limit:
        winner = env.game.determine_winner_by_score()
    else:
        winner = env.game.get_winner()

    for item in trajectory:
        item["outcome"] = outcome_for_player(winner, item["acting_player"])

        if item["value"] is None:
            item["advantage_target"] = None
        else:
            item["advantage_target"] = item["outcome"] - item["value"]

    return {
        "winner": winner,
        "steps": step,
        "is_terminal": env.game.is_terminal(),
        "reached_step_limit": reached_step_limit,
        "final_phase": env.game.phase,
        "final_player": env.game.current_player,
        "trajectory": trajectory,
        "final_board": env.render(),
        "history": env.game.history.copy(),
        "command_log": env.game.command_log.copy(),
    }


def collect_selfplay_episodes(
    red_model: ActorCriticMLP | None,
    blue_model: ActorCriticMLP | None = None,
    n: int = 1,
    max_steps: int = 300,
    device: str = "cpu",
    greedy: bool = False,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for _ in range(n):
        episode = collect_selfplay_episode(
            red_model=red_model,
            blue_model=blue_model,
            max_steps=max_steps,
            device=device,
            greedy=greedy,
        )
        results.append(episode)

    return results