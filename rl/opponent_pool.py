from __future__ import annotations

import random
from typing import Any

import torch

from rl.policy_model import ActorCriticMLP
from rl.selfplay_rollout import collect_selfplay_episode


def clone_actor_critic_model(
    model: ActorCriticMLP,
    device: str = "cpu",
) -> ActorCriticMLP:
    cloned = ActorCriticMLP().to(device)
    cloned.load_state_dict(model.state_dict())
    cloned.eval()
    return cloned


def load_actor_critic_checkpoint(
    checkpoint_path: str,
    device: str = "cpu",
) -> ActorCriticMLP:
    model = ActorCriticMLP().to(device)
    state_dict = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def sample_opponent_from_pool(
    current_model: ActorCriticMLP,
    checkpoint_paths: list[str],
    random_opponent_prob: float = 0.2,
    current_opponent_prob: float = 0.5,
    device: str = "cpu",
) -> dict[str, Any]:
    r = random.random()

    if r < random_opponent_prob:
        return {
            "type": "random",
            "model": None,
            "checkpoint_path": None,
        }

    if r < random_opponent_prob + current_opponent_prob:
        return {
            "type": "current_clone",
            "model": clone_actor_critic_model(current_model, device=device),
            "checkpoint_path": None,
        }

    if checkpoint_paths:
        checkpoint_path = random.choice(checkpoint_paths)
        return {
            "type": "historical_checkpoint",
            "model": load_actor_critic_checkpoint(checkpoint_path, device=device),
            "checkpoint_path": checkpoint_path,
        }

    return {
        "type": "current_clone",
        "model": clone_actor_critic_model(current_model, device=device),
        "checkpoint_path": None,
    }


def collect_training_episode_against_pool(
    current_model: ActorCriticMLP,
    checkpoint_paths: list[str],
    max_steps: int = 300,
    device: str = "cpu",
    greedy: bool = False,
    random_opponent_prob: float = 0.2,
    current_opponent_prob: float = 0.5,
) -> dict[str, Any]:
    current_color = random.choice(["R", "B"])

    opponent_info = sample_opponent_from_pool(
        current_model=current_model,
        checkpoint_paths=checkpoint_paths,
        random_opponent_prob=random_opponent_prob,
        current_opponent_prob=current_opponent_prob,
        device=device,
    )

    opponent_model = opponent_info["model"]

    if current_color == "R":
        red_model = current_model
        blue_model = opponent_model
    else:
        red_model = opponent_model
        blue_model = current_model

    episode = collect_selfplay_episode(
        red_model=red_model,
        blue_model=blue_model,
        max_steps=max_steps,
        device=device,
        greedy=greedy,
    )

    filtered_trajectory = [
        item
        for item in episode["trajectory"]
        if item["acting_player"] == current_color and item["agent_type"] == "actor_critic"
    ]

    episode["trajectory"] = filtered_trajectory
    episode["training_player"] = current_color
    episode["opponent_type"] = opponent_info["type"]
    episode["opponent_checkpoint"] = opponent_info["checkpoint_path"]

    return episode


def collect_training_episodes_against_pool(
    current_model: ActorCriticMLP,
    checkpoint_paths: list[str],
    n: int,
    max_steps: int = 300,
    device: str = "cpu",
    greedy: bool = False,
    random_opponent_prob: float = 0.2,
    current_opponent_prob: float = 0.5,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for _ in range(n):
        episode = collect_training_episode_against_pool(
            current_model=current_model,
            checkpoint_paths=checkpoint_paths,
            max_steps=max_steps,
            device=device,
            greedy=greedy,
            random_opponent_prob=random_opponent_prob,
            current_opponent_prob=current_opponent_prob,
        )
        results.append(episode)

    return results