#train_supervised.py
from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, Dataset

from rl.dataset import build_dataset_from_episodes
from rl.policy_model import PolicyMLP


class PolicyDataset(Dataset):
    def __init__(self, samples: list[dict[str, Any]]) -> None:
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        sample = self.samples[index]

        features = torch.tensor(
            sample["features_before"],
            dtype=torch.float32,
        )
        action_id = torch.tensor(
            sample["action_id"],
            dtype=torch.long,
        )

        return features, action_id


def build_policy_dataset_from_episodes(
    episodes: list[dict[str, Any]],
) -> PolicyDataset:
    samples = build_dataset_from_episodes(episodes)
    return PolicyDataset(samples)


def evaluate_policy_loss(
    model: nn.Module,
    loader: DataLoader,
    device: str = "cpu",
) -> float:
    model.eval()

    total_loss = 0.0
    total_count = 0

    with torch.no_grad():
        for features, action_ids in loader:
            features = features.to(device)
            action_ids = action_ids.to(device)

            logits = model(features)
            loss = F.cross_entropy(logits, action_ids)

            batch_size = features.size(0)
            total_loss += loss.item() * batch_size
            total_count += batch_size

    if total_count == 0:
        return 0.0

    return total_loss / total_count


def train_policy_supervised(
    dataset: Dataset,
    epochs: int = 5,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    device: str = "cpu",
) -> tuple[PolicyMLP, list[dict[str, float]]]:
    if len(dataset) == 0:
        raise ValueError("dataset 为空，无法训练。")

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
    )

    model = PolicyMLP().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    history: list[dict[str, float]] = []

    for epoch in range(1, epochs + 1):
        model.train()

        total_loss = 0.0
        total_count = 0

        for features, action_ids in loader:
            features = features.to(device)
            action_ids = action_ids.to(device)

            logits = model(features)
            loss = F.cross_entropy(logits, action_ids)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            batch_size_now = features.size(0)
            total_loss += loss.item() * batch_size_now
            total_count += batch_size_now

        train_loss = total_loss / total_count
        eval_loss = evaluate_policy_loss(
            model=model,
            loader=loader,
            device=device,
        )

        epoch_record = {
            "epoch": float(epoch),
            "train_loss": float(train_loss),
            "eval_loss": float(eval_loss),
        }
        history.append(epoch_record)

        print(
            f"[Epoch {epoch}] "
            f"train_loss={train_loss:.6f}, "
            f"eval_loss={eval_loss:.6f}"
        )

    return model, history


def save_policy_model(model: nn.Module, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)