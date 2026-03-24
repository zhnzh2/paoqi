#build_dataset.py
from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_match_files(folder: str) -> list[Path]:
    return sorted(Path(folder).rglob("*.json"))

def sample_passes_filters(
    sample: dict,
    mode: str | None,
    only_winner_moves: bool,
    allowed_modes: set[str] | None,
) -> bool:
    if only_winner_moves and not sample.get("is_winner_move", False):
        return False

    if allowed_modes is not None and mode not in allowed_modes:
        return False

    return True

def extract_action_features(action: dict) -> dict:
    return {
        "action_type": action.get("type"),
        "action_mode": action.get("mode"),
        "x": action.get("x"),
        "y": action.get("y"),
        "player": action.get("player"),
        "phase": action.get("phase"),
        "label": action.get("label"),
    }

def encode_action_label(action: dict) -> str:
    action_type = action.get("type")

    if action_type == "move":
        mode = action.get("mode")
        x = action.get("x")
        y = action.get("y")
        return f"move_{mode}_{x}_{y}"

    if action_type == "muzzle":
        cannon_index = action.get("cannon_index")
        direction = action.get("direction")
        return f"muzzle_{cannon_index}_{direction}"

    if action_type == "fire":
        cannon_index = action.get("cannon_index")
        return f"fire_{cannon_index}"

    if action_type == "eat":
        target_index = action.get("target_index")
        return f"eat_{target_index}"

    return "unknown"

def build_dataset_from_folder(
    folder: str,
    only_winner_moves: bool = False,
    allowed_modes: set[str] | None = None,
) -> list[dict]:
    dataset = []
    files = collect_match_files(folder)

    for file_path in files:
        data = load_json(file_path)

        mode = data.get("mode")
        samples = data.get("training_samples", [])

        for sample in samples:
            if not sample_passes_filters(
                sample=sample,
                mode=mode,
                only_winner_moves=only_winner_moves,
                allowed_modes=allowed_modes,
            ):
                continue
            action = sample.get("action", {})
            action_features = extract_action_features(action)
            action_code = encode_action_label(action)

            dataset.append(
                {
                    "source_file": str(file_path),
                    "mode": mode,
                    "step": sample.get("step"),
                    "player": sample.get("player"),
                    "phase": sample.get("phase"),
                    "board": sample.get("board"),
                    "board_numeric": sample.get("board_numeric"),
                    "action": action,
                    "action_type": action_features.get("action_type"),
                    "action_mode": action_features.get("action_mode"),
                    "action_x": action_features.get("x"),
                    "action_y": action_features.get("y"),
                    "action_player": action_features.get("player"),
                    "action_phase": action_features.get("phase"),
                    "action_label": action_features.get("label"),
                    "action_code": action_code,
                    "winner": sample.get("winner"),
                    "is_winner_move": sample.get("is_winner_move"),
                }
            )

    return dataset


def save_dataset(dataset: list[dict], output_path: str) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)


def main() -> None:
    folder = "match_logs"
    output_path = "datasets/training_dataset_v2.json"

    dataset = build_dataset_from_folder(
        folder=folder,
        only_winner_moves=True,
        allowed_modes={"ai_vs_ai", "ai_vs_greedy"},
    )
    save_dataset(dataset, output_path)

    print(f"已收集样本数：{len(dataset)}")
    print(f"已保存到：{output_path}")


if __name__ == "__main__":
    main()