from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_good_game(game_data: dict[str, Any]) -> bool:
    if game_data.get("aborted", False):
        return False

    if game_data.get("steps", 0) <= 0:
        return False

    if not game_data.get("trajectory"):
        return False

    return True


def build_samples_from_one_game(
    game_data: dict[str, Any],
    game_index: int,
    only_human_moves: bool = True,
    only_human_wins: bool = False,
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []

    human_color = game_data["human_color"]
    winner = game_data.get("winner")

    if only_human_wins and winner != human_color:
        return samples

    trajectory = game_data["trajectory"]

    for item in trajectory:
        if only_human_moves and item.get("agent_type") != "human":
            continue

        sample = {
            "game_index": game_index,
            "step": item["step"],
            "acting_player": item["acting_player"],
            "phase_before": item["phase_before"],
            "agent_type": item["agent_type"],
            "action_id": item["action_id"],
            "action_text": item.get("action_text"),
            "features_before": item["features_before"],
            "action_mask": item["action_mask"],
            "winner": winner,
            "human_color": human_color,
            "model_color": game_data["model_color"],
            "is_human_win": (winner == human_color),
            "reached_step_limit": game_data.get("reached_step_limit", False),
            "source_file": game_data.get("_source_file"),
        }

        samples.append(sample)

    return samples


def build_imitation_dataset(
    input_folder: str = "human_game_logs",
    output_path: str = "datasets/imitation/human_imitation_dataset.json",
    only_human_moves: bool = True,
    only_human_wins: bool = False,
) -> dict[str, Any]:
    folder = Path(input_folder)

    if not folder.exists():
        raise FileNotFoundError(f"找不到目录：{input_folder}")

    json_files = sorted(folder.glob("*.json"))

    if not json_files:
        raise ValueError(f"目录 {input_folder} 中没有 json 文件。")

    all_samples: list[dict[str, Any]] = []
    used_files: list[str] = []
    skipped_files: list[str] = []

    total_games = 0
    good_games = 0

    for game_index, path in enumerate(json_files, start=1):
        total_games += 1

        game_data = load_json(path)
        game_data["_source_file"] = str(path)

        if not is_good_game(game_data):
            skipped_files.append(str(path))
            continue

        good_games += 1
        used_files.append(str(path))

        samples = build_samples_from_one_game(
            game_data=game_data,
            game_index=game_index,
            only_human_moves=only_human_moves,
            only_human_wins=only_human_wins,
        )
        all_samples.extend(samples)

    if not all_samples:
        raise ValueError("没有提取到任何样本，请检查筛选条件是否过严。")

    dataset = {
        "meta": {
            "input_folder": input_folder,
            "total_games_found": total_games,
            "good_games_used": good_games,
            "only_human_moves": only_human_moves,
            "only_human_wins": only_human_wins,
            "sample_count": len(all_samples),
            "used_files": used_files,
            "skipped_files": skipped_files,
        },
        "samples": all_samples,
    }

    save_json(dataset, output_path)
    return dataset


def main() -> None:
    dataset = build_imitation_dataset(
        input_folder="human_game_logs",
        output_path="datasets/imitation/human_imitation_dataset.json",
        only_human_moves=True,
        only_human_wins=False,
    )

    meta = dataset["meta"]

    print("imitation 数据集已生成。")
    print(f"总文件数：{meta['total_games_found']}")
    print(f"有效对局数：{meta['good_games_used']}")
    print(f"样本数：{meta['sample_count']}")
    print(f"输出文件：datasets/imitation/human_imitation_dataset.json")


if __name__ == "__main__":
    main()