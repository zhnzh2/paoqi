from __future__ import annotations

import json
from pathlib import Path


def load_match(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_match_summary(data: dict) -> None:
    print("=== 对局信息 ===")
    print(f"模式：{data.get('mode')}")
    print(f"胜者：{data.get('winner')}")
    print(f"步数：{data.get('steps')}")
    print(f"正常终局：{data.get('terminal')}")
    print(f"步数上限结算：{data.get('reached_step_limit')}")
    print(f"红方得分：{data.get('red_score')}")
    print(f"蓝方得分：{data.get('blue_score')}")

    if "red_depth" in data:
        print(f"红方深度：{data.get('red_depth')}")
    if "blue_depth" in data:
        print(f"蓝方深度：{data.get('blue_depth')}")

    print()


def print_final_board(data: dict) -> None:
    print("=== 终局棋盘 ===")
    print(data.get("final_board", ""))
    print()


def print_history(data: dict) -> None:
    print("=== 完整棋谱 ===")
    print(data.get("history_text", ""))
    print()

def print_action_log(data: dict) -> None:
    print("=== 逐步动作 ===")
    action_log = data.get("action_log", [])

    if not action_log:
        print("没有动作列表")
        print()
        return

    for item in action_log:
        step = item.get("step")
        player = item.get("player")
        action = item.get("action", {})
        label = action.get("label", str(action))
        print(f"Step {step}: 玩家 {player} -> {label}")

    print()

def print_training_samples_preview(data: dict, limit: int = 10) -> None:
    print("=== 训练样本预览 ===")
    samples = data.get("training_samples", [])

    if not samples:
        print("没有 training_samples")
        print()
        return

    for item in samples[:limit]:
        step = item.get("step")
        player = item.get("player")
        phase = item.get("phase")
        winner = item.get("winner")
        is_winner_move = item.get("is_winner_move")
        action = item.get("action", {})
        label = action.get("label", str(action))

        print(
            f"Step {step}: 玩家 {player}, phase={phase} -> {label}, "
            f"winner={winner}, is_winner_move={is_winner_move}"
        )

    if len(samples) > limit:
        print(f"... 共 {len(samples)} 条，只显示前 {limit} 条")

    print()

def replay_match(path: str) -> None:
    data = load_match(path)

    print(f"文件：{Path(path)}")
    print()

    print_match_summary(data)
    print_final_board(data)
    print_action_log(data)
    print_training_samples_preview(data)
    print_history(data)


if __name__ == "__main__":
    replay_match("match_logs/ai_vs_greedy/ai_vs_greedy_20260325_020437_139611.json")