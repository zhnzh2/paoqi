#train_actor_critic.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

from rl.opponent_pool import collect_training_episodes_against_pool
from rl.policy_model import ActorCriticMLP, apply_action_mask_to_logits


def build_actor_critic_batch(
    episodes: list[dict[str, Any]],
    device: str = "cpu",
) -> dict[str, torch.Tensor]:
    features_list: list[list[float]] = []
    action_mask_list: list[list[float]] = []
    action_id_list: list[int] = []
    outcome_list: list[float] = []
    advantage_target_list: list[float] = []

    for episode in episodes:
        for item in episode["trajectory"]:
            if item["value"] is None or item["advantage_target"] is None:
                continue

            features_list.append(item["features_before"])
            action_mask_list.append(item["action_mask"])
            action_id_list.append(item["action_id"])
            outcome_list.append(item["outcome"])
            advantage_target_list.append(item["advantage_target"])

    if not features_list:
        raise ValueError("episodes 中没有可训练样本。")

    features = torch.tensor(features_list, dtype=torch.float32, device=device)
    action_masks = torch.tensor(action_mask_list, dtype=torch.float32, device=device)
    action_ids = torch.tensor(action_id_list, dtype=torch.long, device=device)
    outcomes = torch.tensor(outcome_list, dtype=torch.float32, device=device)
    advantage_targets = torch.tensor(
        advantage_target_list,
        dtype=torch.float32,
        device=device,
    )

    return {
        "features": features,
        "action_masks": action_masks,
        "action_ids": action_ids,
        "outcomes": outcomes,
        "advantage_targets": advantage_targets,
    }


def save_actor_critic_model(model: ActorCriticMLP, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)


def save_json(data: Any, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_episode_history_dump(
    episodes: list[dict[str, Any]],
    iteration: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for i, episode in enumerate(episodes, start=1):
        result.append(
            {
                "iteration": iteration,
                "episode_index": i,
                "winner": episode["winner"],
                "steps": episode["steps"],
                "is_terminal": episode["is_terminal"],
                "reached_step_limit": episode.get("reached_step_limit", False),
                "training_player": episode.get("training_player"),
                "opponent_type": episode.get("opponent_type"),
                "opponent_checkpoint": episode.get("opponent_checkpoint"),
                "history": episode.get("history", []),
                "command_log": episode.get("command_log", []),
            }
        )

    return result


def train_actor_critic_selfplay(
    iterations: int = 50,
    episodes_per_iteration: int = 20,
    max_steps: int = 300,
    learning_rate: float = 1e-3,
    value_coef: float = 0.5,
    entropy_coef: float = 0.01,
    save_every: int = 10,
    checkpoint_dir: str = "checkpoints/actor_critic_pool",
    random_opponent_prob: float = 0.2,
    current_opponent_prob: float = 0.5,
    history_save_dir: str | None = "logs/actor_critic_histories",
    history_json_path: str | None = "logs/actor_critic_history.json",
    device: str = "cpu",
) -> tuple[ActorCriticMLP, list[dict[str, float]]]:
    model = ActorCriticMLP().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    history: list[dict[str, float]] = []
    historical_checkpoints: list[str] = []

    for iteration in range(1, iterations + 1):
        episodes = collect_training_episodes_against_pool(
            current_model=model,
            checkpoint_paths=historical_checkpoints,
            n=episodes_per_iteration,
            max_steps=max_steps,
            device=device,
            greedy=False,
            random_opponent_prob=random_opponent_prob,
            current_opponent_prob=current_opponent_prob,
        )

        batch = build_actor_critic_batch(
            episodes=episodes,
            device=device,
        )

        features = batch["features"]
        action_masks = batch["action_masks"]
        action_ids = batch["action_ids"]
        outcomes = batch["outcomes"]
        advantage_targets = batch["advantage_targets"]

        model.train()

        output = model(features)
        policy_logits = output["policy_logits"]
        state_values = output["state_value"]

        masked_logits = apply_action_mask_to_logits(policy_logits, action_masks)
        dist = torch.distributions.Categorical(logits=masked_logits)

        log_probs = dist.log_prob(action_ids)
        entropy = dist.entropy().mean()

        policy_loss = -(log_probs * advantage_targets.detach()).mean()
        value_loss = F.mse_loss(state_values, outcomes)
        total_loss = policy_loss + value_coef * value_loss - entropy_coef * entropy

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        avg_steps = sum(item["steps"] for item in episodes) / len(episodes)

        winner_list = [item["winner"] for item in episodes]
        red_win = sum(1 for w in winner_list if w == "R")
        blue_win = sum(1 for w in winner_list if w == "B")
        draw = sum(1 for w in winner_list if w is None)

        random_opp_count = sum(1 for e in episodes if e["opponent_type"] == "random")
        current_clone_count = sum(1 for e in episodes if e["opponent_type"] == "current_clone")
        historical_count = sum(1 for e in episodes if e["opponent_type"] == "historical_checkpoint")

        reached_step_limit_count = sum(
            1 for e in episodes if e.get("reached_step_limit", False)
        )

        model_win = 0
        model_loss = 0
        model_draw = 0

        for episode in episodes:
            training_player = episode["training_player"]
            winner = episode["winner"]

            if winner is None:
                model_draw += 1
            elif winner == training_player:
                model_win += 1
            else:
                model_loss += 1

        model_win_rate = model_win / len(episodes)
        model_loss_rate = model_loss / len(episodes)
        model_draw_rate = model_draw / len(episodes)
        step_limit_rate = reached_step_limit_count / len(episodes)

        record = {
            "iteration": float(iteration),
            "total_loss": float(total_loss.item()),
            "policy_loss": float(policy_loss.item()),
            "value_loss": float(value_loss.item()),
            "entropy": float(entropy.item()),
            "avg_steps": float(avg_steps),
            "red_win": float(red_win),
            "blue_win": float(blue_win),
            "draw": float(draw),
            "model_win": float(model_win),
            "model_loss": float(model_loss),
            "model_draw": float(model_draw),
            "model_win_rate": float(model_win_rate),
            "model_loss_rate": float(model_loss_rate),
            "model_draw_rate": float(model_draw_rate),
            "reached_step_limit_count": float(reached_step_limit_count),
            "step_limit_rate": float(step_limit_rate),
            "random_opp_count": float(random_opp_count),
            "current_clone_count": float(current_clone_count),
            "historical_count": float(historical_count),
        }
        history.append(record)

        print(
            f"[Iteration {iteration}] "
            f"total_loss={record['total_loss']:.6f}, "
            f"policy_loss={record['policy_loss']:.6f}, "
            f"value_loss={record['value_loss']:.6f}, "
            f"entropy={record['entropy']:.6f}, "
            f"avg_steps={record['avg_steps']:.2f}, "
            f"R={red_win}, B={blue_win}, D={draw}, "
            f"model_win_rate={model_win_rate:.3f}, "
            f"step_limit={reached_step_limit_count}/{len(episodes)}, "
            f"opp(random/current/history)="
            f"{random_opp_count}/{current_clone_count}/{historical_count}"
        )

        if history_json_path is not None:
            save_json(history, history_json_path)

        if history_save_dir is not None:
            episode_dump = build_episode_history_dump(episodes, iteration)
            save_json(
                episode_dump,
                f"{history_save_dir}/iter_{iteration}.json",
            )

        if iteration % save_every == 0:
            checkpoint_path = f"{checkpoint_dir}/actor_critic_iter_{iteration}.pt"
            save_actor_critic_model(model, checkpoint_path)
            historical_checkpoints.append(checkpoint_path)
            print(f"已保存 checkpoint: {checkpoint_path}")

    return model, history