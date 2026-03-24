#inspect_dataset.py
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def load_dataset(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def inspect_dataset(path: str) -> None:
    data = load_dataset(path)

    mode_counter = Counter()
    action_type_counter = Counter()
    action_code_counter = Counter()
    phase_counter = Counter()
    player_counter = Counter()
    winner_move_counter = Counter()

    for item in data:
        mode_counter[item.get("mode")] += 1
        action_type_counter[item.get("action_type")] += 1
        action_code_counter[item.get("action_code")] += 1
        phase_counter[item.get("phase")] += 1
        player_counter[item.get("player")] += 1
        winner_move_counter[item.get("is_winner_move")] += 1

    print("=== 数据集概况 ===")
    print(f"文件：{Path(path)}")
    print(f"总样本数：{len(data)}")
    print()

    print("=== mode 分布 ===")
    for key, value in mode_counter.items():
        print(f"{key}: {value}")
    print()

    print("=== player 分布 ===")
    for key, value in player_counter.items():
        print(f"{key}: {value}")
    print()

    print("=== phase 分布 ===")
    for key, value in phase_counter.items():
        print(f"{key}: {value}")
    print()

    print("=== action_type 分布 ===")
    for key, value in action_type_counter.items():
        print(f"{key}: {value}")
    print()

    print("=== is_winner_move 分布 ===")
    for key, value in winner_move_counter.items():
        print(f"{key}: {value}")
    print()

    print("=== 最常见 action_code 前 20 个 ===")
    for key, value in action_code_counter.most_common(20):
        print(f"{key}: {value}")
    print()


if __name__ == "__main__":
    inspect_dataset("datasets/training_dataset_v2.json")