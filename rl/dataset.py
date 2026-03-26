#dataset.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FEATURE_DIM = 100


def flatten_board_numeric(board_numeric: list[list[int]]) -> list[int]:
    flat: list[int] = []

    for row in board_numeric:
        flat.extend(row)

    return flat


def flatten_phase_one_hot(phase_one_hot: dict[str, int]) -> list[int]:
    return [
        phase_one_hot["is_drop"],
        phase_one_hot["is_muzzle"],
        phase_one_hot["is_fire"],
        phase_one_hot["is_eat"],
    ]


def flatten_player_flags(player_flags: dict[str, int]) -> list[int]:
    return [
        player_flags["current_player_is_red"],
        player_flags["current_player_is_blue"],
        player_flags["round_drop_player_is_red"],
        player_flags["round_drop_player_is_blue"],
    ]


def flatten_scalar_features(scalar_features: dict[str, int]) -> list[int]:
    return [
        scalar_features["turn_number"],
        scalar_features["chain_pass_count"],
        scalar_features["game_over"],
        scalar_features["winner_red"],
        scalar_features["winner_blue"],
        scalar_features["winner_none"],
        scalar_features["red_score"],
        scalar_features["blue_score"],
        scalar_features["legal_action_count"],
        scalar_features["pending_muzzle_count"],
        scalar_features["fire_pool_count"],
    ]


def flatten_observation(obs: dict[str, Any]) -> list[int]:
    board_part = flatten_board_numeric(obs["board_numeric"])
    phase_part = flatten_phase_one_hot(obs["phase_one_hot"])
    player_part = flatten_player_flags(obs["player_flags"])
    scalar_part = flatten_scalar_features(obs["scalar_features"])

    features = board_part + phase_part + player_part + scalar_part

    if len(features) != FEATURE_DIM:
        raise ValueError(
            f"特征长度不正确：期望 {FEATURE_DIM}，实际 {len(features)}"
        )

    return features


def build_dataset_from_episode(
    episode: dict[str, Any],
) -> list[dict[str, Any]]:
    winner = episode["winner"]
    samples: list[dict[str, Any]] = []

    for item in episode["trajectory"]:
        acting_player = item["acting_player"]
        obs_before = item["obs_before"]
        obs_after = item["obs_after"]

        sample = {
            "step": item["step"],
            "acting_player": acting_player,
            "phase_before": item["phase_before"],
            "action_id": item["action_id"],
            "reward": item["reward"],
            "done": item["done"],
            "winner": winner,
            "is_winner_move": (
                winner is not None and acting_player == winner
            ),
            "obs_before": obs_before,
            "obs_after": obs_after,
            "features_before": flatten_observation(obs_before),
            "features_after": flatten_observation(obs_after),
        }

        samples.append(sample)

    return samples


def build_dataset_from_episodes(
    episodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    dataset: list[dict[str, Any]] = []

    for episode_index, episode in enumerate(episodes, start=1):
        episode_samples = build_dataset_from_episode(episode)

        for sample in episode_samples:
            sample["episode_index"] = episode_index

        dataset.extend(episode_samples)

    return dataset


def save_dataset_json(dataset: list[dict[str, Any]], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)


def load_dataset_json(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)