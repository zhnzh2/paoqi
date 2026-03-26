#rollout.py
from __future__ import annotations

import random
from typing import Any

from rl.env import PaoqiEnv


def sample_random_action_id(action_mask: list[int]) -> int:
    legal_action_ids = [
        action_id
        for action_id, flag in enumerate(action_mask)
        if flag == 1
    ]

    if not legal_action_ids:
        raise ValueError("当前没有合法动作，无法随机采样。")

    return random.choice(legal_action_ids)


def collect_episode(
    max_steps: int = 300,
    seed: int | None = None,
) -> dict[str, Any]:
    if seed is not None:
        random.seed(seed)

    env = PaoqiEnv()
    obs, info = env.reset()

    trajectory: list[dict[str, Any]] = []
    step = 0

    while step < max_steps:
        action_mask = info["action_mask"]

        if sum(action_mask) == 0:
            break

        acting_player = info["current_player"]
        phase_before = info["phase"]
        obs_before = obs

        action_id = sample_random_action_id(action_mask)

        next_obs, reward, done, next_info = env.step(action_id)

        trajectory.append(
            {
                "step": step + 1,
                "acting_player": acting_player,
                "phase_before": phase_before,
                "obs_before": obs_before,
                "action_id": action_id,
                "reward": reward,
                "done": done,
                "obs_after": next_obs,
                "winner_after_step": next_info["winner"],
            }
        )

        obs = next_obs
        info = next_info
        step += 1

        if done:
            break

    final_winner = info["winner"]
    final_board = env.render()

    return {
        "steps": step,
        "winner": final_winner,
        "is_terminal": env.game.is_terminal(),
        "final_phase": env.game.phase,
        "final_player": env.game.current_player,
        "trajectory": trajectory,
        "final_board": final_board,
    }


def collect_episodes(
    n: int,
    max_steps: int = 300,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    if n <= 0:
        return []

    results: list[dict[str, Any]] = []

    for i in range(n):
        episode_seed = None if seed is None else seed + i
        result = collect_episode(
            max_steps=max_steps,
            seed=episode_seed,
        )
        results.append(result)

    return results