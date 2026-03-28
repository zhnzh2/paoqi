from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

from rl.policy_model import ActorCriticMLP, apply_action_mask_to_logits


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_model(model: ActorCriticMLP, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)


def load_model_weights(
    model: ActorCriticMLP,
    checkpoint_path: str,
    device: str = "cpu",
) -> None:
    state_dict = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state_dict)


def split_dataset(
    samples: list[dict[str, Any]],
    train_ratio: float = 0.8,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data = samples.copy()
    random.Random(seed).shuffle(data)

    split_index = int(len(data) * train_ratio)
    train_samples = data[:split_index]
    valid_samples = data[split_index:]

    return train_samples, valid_samples


def make_batch(
    samples: list[dict[str, Any]],
    device: str = "cpu",
) -> dict[str, torch.Tensor]:
    features = torch.tensor(
        [item["features_before"] for item in samples],
        dtype=torch.float32,
        device=device,
    )
    action_masks = torch.tensor(
        [item["action_mask"] for item in samples],
        dtype=torch.float32,
        device=device,
    )
    action_ids = torch.tensor(
        [item["action_id"] for item in samples],
        dtype=torch.long,
        device=device,
    )

    return {
        "features": features,
        "action_masks": action_masks,
        "action_ids": action_ids,
    }


def evaluate_imitation(
    model: ActorCriticMLP,
    samples: list[dict[str, Any]],
    device: str = "cpu",
) -> dict[str, float]:
    if not samples:
        return {
            "loss": 0.0,
            "accuracy": 0.0,
        }

    model.eval()

    batch = make_batch(samples, device=device)

    with torch.no_grad():
        output = model(batch["features"])
        logits = output["policy_logits"]
        masked_logits = apply_action_mask_to_logits(logits, batch["action_masks"])

        loss = F.cross_entropy(masked_logits, batch["action_ids"])

        pred = torch.argmax(masked_logits, dim=1)
        acc = (pred == batch["action_ids"]).float().mean().item()

    return {
        "loss": float(loss.item()),
        "accuracy": float(acc),
    }


def append_version_history(
    history_path: str,
    record: dict[str, Any],
) -> None:
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(record)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def train_imitation_policy(
    dataset_path: str = "datasets/imitation/human_imitation_dataset.json",
    model_name: str = "A1",
    base_model_path: str | None = None,
    output_dir: str = "checkpoints/versioned",
    version_history_path: str = "checkpoints/versioned/version_history.json",
    epochs: int = 50,
    learning_rate: float = 1e-3,
    train_ratio: float = 0.8,
    seed: int = 42,
    device: str = "cpu",
) -> tuple[ActorCriticMLP, list[dict[str, float]]]:
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    output_model_path = str(output_dir_path / f"{model_name}.pt")
    output_train_history_path = str(output_dir_path / f"{model_name}_train_history.json")

    dataset = load_json(dataset_path)
    samples = dataset["samples"]

    if not samples:
        raise ValueError("数据集为空，无法训练。")

    train_samples, valid_samples = split_dataset(
        samples=samples,
        train_ratio=train_ratio,
        seed=seed,
    )

    print(f"模型名称：{model_name}")
    print(f"基础模型：{base_model_path}")
    print(f"总样本数：{len(samples)}")
    print(f"训练样本数：{len(train_samples)}")
    print(f"验证样本数：{len(valid_samples)}")

    model = ActorCriticMLP().to(device)

    if base_model_path is not None:
        print(f"正在加载基础模型：{base_model_path}")
        load_model_weights(
            model=model,
            checkpoint_path=base_model_path,
            device=device,
        )

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    train_batch = make_batch(train_samples, device=device)

    history: list[dict[str, float]] = []
    best_valid_acc = -1.0

    for epoch in range(1, epochs + 1):
        model.train()

        output = model(train_batch["features"])
        logits = output["policy_logits"]
        masked_logits = apply_action_mask_to_logits(
            logits,
            train_batch["action_masks"],
        )

        loss = F.cross_entropy(masked_logits, train_batch["action_ids"])

        pred = torch.argmax(masked_logits, dim=1)
        train_acc = (pred == train_batch["action_ids"]).float().mean().item()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        valid_metrics = evaluate_imitation(
            model=model,
            samples=valid_samples,
            device=device,
        )

        record = {
            "epoch": float(epoch),
            "train_loss": float(loss.item()),
            "train_accuracy": float(train_acc),
            "valid_loss": float(valid_metrics["loss"]),
            "valid_accuracy": float(valid_metrics["accuracy"]),
        }
        history.append(record)

        print(
            f"[Epoch {epoch}] "
            f"train_loss={record['train_loss']:.6f}, "
            f"train_acc={record['train_accuracy']:.4f}, "
            f"valid_loss={record['valid_loss']:.6f}, "
            f"valid_acc={record['valid_accuracy']:.4f}"
        )

        if record["valid_accuracy"] > best_valid_acc:
            best_valid_acc = record["valid_accuracy"]
            save_model(model, output_model_path)

    save_json(history, output_train_history_path)

    version_record = {
        "model_name": model_name,
        "train_type": "imitation",
        "base_model_path": base_model_path,
        "dataset_path": dataset_path,
        "sample_count": len(samples),
        "train_sample_count": len(train_samples),
        "valid_sample_count": len(valid_samples),
        "epochs": epochs,
        "learning_rate": learning_rate,
        "train_ratio": train_ratio,
        "seed": seed,
        "best_valid_accuracy": best_valid_acc,
        "output_model_path": output_model_path,
        "output_train_history_path": output_train_history_path,
    }
    append_version_history(version_history_path, version_record)

    print(f"最佳验证集准确率：{best_valid_acc:.4f}")
    print(f"模型已保存到：{output_model_path}")
    print(f"训练历史已保存到：{output_train_history_path}")
    print(f"版本记录已写入：{version_history_path}")

    return model, history


def main() -> None:
    train_imitation_policy(
        dataset_path="datasets/imitation/human_imitation_dataset.json",
        model_name="A3",
        base_model_path="checkpoints/versioned/A2.pt",
        output_dir="checkpoints/versioned",
        version_history_path="checkpoints/versioned/version_history.json",
        epochs=50,
        learning_rate=1e-3,
        train_ratio=0.8,
        seed=42,
        device="cpu",
    )


if __name__ == "__main__":
    main()