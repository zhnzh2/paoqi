from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.game import Game
from main import parse_input_to_action, print_help
from rl.action_codec import encode_action, get_action_mask, get_legal_action_id_map
from rl.dataset import flatten_observation
from rl.eval_actor_critic import load_actor_critic_from_checkpoint
from rl.policy_model import select_action_id_from_actor_critic
from rl.state_codec import encode_state


def save_json(data: Any, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def print_phase_prompt(game: Game) -> None:
    print(game.phase_name())

    if game.phase == "fire":
        print(game.fireable_report())
    elif game.phase == "eat":
        print(game.capturable_report())
    elif game.phase == "muzzle":
        print(game.pending_muzzle_report())


def action_equal_for_execution(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a.get("type") != b.get("type"):
        return False

    action_type = a["type"]

    if action_type == "move":
        return (
            a.get("mode") == b.get("mode")
            and a.get("x") == b.get("x")
            and a.get("y") == b.get("y")
        )

    if action_type == "muzzle":
        return (
            a.get("index") == b.get("index")
            and a.get("direction") == b.get("direction")
        )

    if action_type == "fire":
        return a.get("index") == b.get("index")

    if action_type == "eat":
        return a.get("index") == b.get("index")

    return False


def resolve_human_action_and_id(
    game: Game,
    raw_text: str,
) -> tuple[dict[str, Any], int]:
    parsed_action = parse_input_to_action(game, raw_text)
    if parsed_action is None:
        raise ValueError("无法识别该输入，请重新输入。")

    legal_action_id_map = get_legal_action_id_map(game)

    for action_id, legal_action in legal_action_id_map.items():
        if action_equal_for_execution(parsed_action, legal_action):
            return legal_action, action_id

    raise ValueError(f"当前输入对应的动作不合法：{parsed_action}")


def choose_model_action(
    game: Game,
    model: Any,
    greedy: bool = True,
    device: str = "cpu",
) -> tuple[dict[str, Any], int, float]:
    obs = encode_state(game)
    features = flatten_observation(obs)
    action_mask = get_action_mask(game)

    result = select_action_id_from_actor_critic(
        model=model,
        features=features,
        action_mask=action_mask,
        greedy=greedy,
        device=device,
    )

    action_id = result["action_id"]
    legal_action = get_legal_action_id_map(game)[action_id]
    state_value = float(result["state_value"].item())

    return legal_action, action_id, state_value


def next_game_index(folder: str, prefix: str = "human_vs_model") -> int:
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)

    max_index = 0
    for file in path.glob(f"{prefix}_*.json"):
        stem = file.stem
        tail = stem.replace(f"{prefix}_", "")
        if tail.isdigit():
            max_index = max(max_index, int(tail))

    return max_index + 1


def run_human_vs_model_game(
    checkpoint_path: str,
    human_color: str = "R",
    max_steps: int = 300,
    greedy: bool = True,
    device: str = "cpu",
    output_folder: str = "human_game_logs",
) -> dict[str, Any]:
    if human_color not in ("R", "B"):
        raise ValueError("human_color 只能是 'R' 或 'B'。")

    model_color = "B" if human_color == "R" else "R"
    model = load_actor_critic_from_checkpoint(
        checkpoint_path=checkpoint_path,
        device=device,
    )

    game = Game()
    trajectory: list[dict[str, Any]] = []
    step = 0

    print("欢迎进入 人机对局采集模式。")
    print(f"你执 {human_color} 方，模型执 {model_color} 方。")
    print(f"模型 checkpoint: {checkpoint_path}")
    print_help()
    print()

    while step < max_steps and not game.is_terminal():
        print(game.board.render())
        print()
        print(game.status_text())
        print()
        print_phase_prompt(game)

        obs_before = encode_state(game)
        features_before = flatten_observation(obs_before)
        action_mask = get_action_mask(game)

        if sum(action_mask) == 0:
            print("当前没有合法动作，提前结束。")
            break

        acting_player = game.current_player
        phase_before = game.phase

        if acting_player == human_color:
            while True:
                raw = input("请输入你的动作 > ").strip()

                if not raw:
                    print("请输入有效命令。")
                    continue

                lowered = raw.lower()

                if lowered == "help":
                    print_help()
                    print()
                    continue

                if lowered == "legal":
                    legal_info = game.get_legal_actions_snapshot()
                    print("当前所有合法动作：")
                    print(
                        f"  当前阶段：{legal_info['phase']} | "
                        f"行动方：{legal_info['current_player']} | "
                        f"动作数：{legal_info['count']}"
                    )
                    for action in legal_info["actions"]:
                        print(" ", action["label"])
                    print()
                    continue

                if lowered == "record":
                    print(game.history_text())
                    print()
                    continue

                if lowered == "ops":
                    print(game.command_log_text())
                    print()
                    continue

                if lowered == "quit":
                    print("你选择中途退出，本局将立即结束并保存当前结果。")
                    reached_step_limit = False
                    winner = None
                    result = {
                        "winner": winner,
                        "steps": step,
                        "is_terminal": game.is_terminal(),
                        "reached_step_limit": reached_step_limit,
                        "human_color": human_color,
                        "model_color": model_color,
                        "checkpoint_path": checkpoint_path,
                        "history": game.history.copy(),
                        "command_log": game.command_log.copy(),
                        "final_board": game.board.render(),
                        "trajectory": trajectory,
                        "aborted": True,
                    }

                    game_index = next_game_index(output_folder)
                    save_json(
                        result,
                        f"{output_folder}/human_vs_model_{game_index:03d}.json",
                    )
                    print(
                        f"已保存到 "
                        f"{output_folder}/human_vs_model_{game_index:03d}.json"
                    )
                    return result

                try:
                    legal_action, action_id = resolve_human_action_and_id(game, raw)
                except Exception as e:
                    print(f"输入无效：{e}")
                    print()
                    continue

                game.apply_action(legal_action)
                print("执行后棋盘：")
                # print(game.board.render())
                print()

                agent_type = "human"
                state_value = None
                action_text = raw
                break

        else:
            legal_action, action_id, state_value = choose_model_action(
                game=game,
                model=model,
                greedy=greedy,
                device=device,
            )
            game.apply_action(legal_action)
            agent_type = "model"
            action_text = game.action_to_command_text(legal_action)

            print(f"模型动作：{action_text}")
            print("执行后棋盘：")
            # print(game.board.render())
            print()

        obs_after = encode_state(game)

        trajectory.append(
            {
                "step": step + 1,
                "acting_player": acting_player,
                "phase_before": phase_before,
                "agent_type": agent_type,
                "action_id": action_id,
                "action": legal_action,
                "action_text": action_text,
                "state_value": state_value,
                "action_mask": action_mask.copy(),
                "obs_before": obs_before,
                "obs_after": obs_after,
                "features_before": features_before,
            }
        )

        step += 1

    reached_step_limit = (not game.is_terminal() and step >= max_steps)

    if reached_step_limit:
        winner = game.determine_winner_by_score()
    else:
        winner = game.get_winner()

    result = {
        "winner": winner,
        "steps": step,
        "is_terminal": game.is_terminal(),
        "reached_step_limit": reached_step_limit,
        "human_color": human_color,
        "model_color": model_color,
        "checkpoint_path": checkpoint_path,
        "history": game.history.copy(),
        "command_log": game.command_log.copy(),
        "final_board": game.board.render(),
        "trajectory": trajectory,
        "aborted": False,
    }

    game_index = next_game_index(output_folder)
    save_json(
        result,
        f"{output_folder}/human_vs_model_{game_index:03d}.json",
    )

    print(game.board.render())
    print()
    print("对局结束。")
    print(f"winner = {winner}")
    print(f"steps = {step}")
    print(f"reached_step_limit = {reached_step_limit}")
    print(f"已保存到 {output_folder}/human_vs_model_{game_index:03d}.json")

    return result