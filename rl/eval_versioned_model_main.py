from __future__ import annotations

from typing import Any

from rl.eval_actor_critic import (
    evaluate_actor_critic_vs_random_balanced,
    load_actor_critic_from_checkpoint,
    save_json,
)
from rl.env import PaoqiEnv
from rl.dataset import flatten_observation
from rl.policy_model import select_action_id_from_actor_critic


def choose_action_for_model(
    model: Any,
    env: PaoqiEnv,
    greedy: bool = True,
    device: str = "cpu",
) -> dict[str, Any]:
    obs = env.get_observation()
    features = flatten_observation(obs)
    action_mask = env.get_action_mask()

    return select_action_id_from_actor_critic(
        model=model,
        features=features,
        action_mask=action_mask,
        greedy=greedy,
        device=device,
    )


def run_model_vs_model_game(
    red_model: Any,
    blue_model: Any,
    max_steps: int = 300,
    greedy: bool = True,
    device: str = "cpu",
) -> dict[str, Any]:
    env = PaoqiEnv()
    obs, info = env.reset()

    step = 0
    action_log: list[dict[str, Any]] = []

    while step < max_steps and not env.game.is_terminal():
        current_player = info["current_player"]
        action_mask = info["action_mask"]

        if sum(action_mask) == 0:
            break

        if current_player == "R":
            current_model = red_model
            agent_name = "red_model"
        else:
            current_model = blue_model
            agent_name = "blue_model"

        action_result = choose_action_for_model(
            model=current_model,
            env=env,
            greedy=greedy,
            device=device,
        )
        action_id = action_result["action_id"]
        state_value = float(action_result["state_value"].item())

        obs, reward, done, info = env.step(action_id)

        action_log.append(
            {
                "step": step + 1,
                "player": current_player,
                "agent_name": agent_name,
                "action_id": action_id,
                "state_value": state_value,
                "reward": reward,
                "done": done,
            }
        )

        step += 1

        if done:
            break

    reached_step_limit = (not env.game.is_terminal() and step >= max_steps)

    if reached_step_limit:
        winner = env.game.determine_winner_by_score()
    else:
        winner = env.game.get_winner()

    return {
        "winner": winner,
        "steps": step,
        "is_terminal": env.game.is_terminal(),
        "reached_step_limit": reached_step_limit,
        "final_board": env.render(),
        "history": env.game.history.copy(),
        "command_log": env.game.command_log.copy(),
        "action_log": action_log,
    }


def summarize_balanced_results(
    results: list[dict[str, Any]],
    tested_model_name: str,
    tested_model_color_list: list[str],
) -> dict[str, Any]:
    total_games = len(results)

    tested_model_win = 0
    opponent_win = 0
    draw = 0
    reached_step_limit_count = 0
    total_steps = 0

    for result, tested_color in zip(results, tested_model_color_list):
        winner = result["winner"]

        if winner == tested_color:
            tested_model_win += 1
        elif winner is None:
            draw += 1
        else:
            opponent_win += 1

        if result["reached_step_limit"]:
            reached_step_limit_count += 1

        total_steps += result["steps"]

    avg_steps = total_steps / total_games if total_games > 0 else 0.0

    return {
        "tested_model_name": tested_model_name,
        "total_games": total_games,
        "tested_model_win": tested_model_win,
        "opponent_win": opponent_win,
        "draw": draw,
        "tested_model_win_rate": tested_model_win / total_games if total_games > 0 else 0.0,
        "opponent_win_rate": opponent_win / total_games if total_games > 0 else 0.0,
        "draw_rate": draw / total_games if total_games > 0 else 0.0,
        "avg_steps": avg_steps,
        "reached_step_limit_count": reached_step_limit_count,
        "step_limit_rate": reached_step_limit_count / total_games if total_games > 0 else 0.0,
        "results": results,
    }


def evaluate_model_vs_model_balanced(
    tested_model_path: str,
    opponent_model_path: str,
    tested_model_name: str = "A4",
    opponent_model_name: str = "A3",
    n_games_per_color: int = 20,
    max_steps: int = 300,
    greedy: bool = True,
    device: str = "cpu",
) -> dict[str, Any]:
    tested_model = load_actor_critic_from_checkpoint(
        checkpoint_path=tested_model_path,
        device=device,
    )
    opponent_model = load_actor_critic_from_checkpoint(
        checkpoint_path=opponent_model_path,
        device=device,
    )

    all_results: list[dict[str, Any]] = []
    tested_model_color_list: list[str] = []

    # tested model as Red
    for _ in range(n_games_per_color):
        result = run_model_vs_model_game(
            red_model=tested_model,
            blue_model=opponent_model,
            max_steps=max_steps,
            greedy=greedy,
            device=device,
        )
        all_results.append(result)
        tested_model_color_list.append("R")

    # tested model as Blue
    for _ in range(n_games_per_color):
        result = run_model_vs_model_game(
            red_model=opponent_model,
            blue_model=tested_model,
            max_steps=max_steps,
            greedy=greedy,
            device=device,
        )
        all_results.append(result)
        tested_model_color_list.append("B")

    summary = summarize_balanced_results(
        results=all_results,
        tested_model_name=tested_model_name,
        tested_model_color_list=tested_model_color_list,
    )
    summary["tested_model_path"] = tested_model_path
    summary["opponent_model_path"] = opponent_model_path
    summary["opponent_model_name"] = opponent_model_name
    summary["n_games_per_color"] = n_games_per_color
    summary["max_steps"] = max_steps
    summary["greedy"] = greedy

    return summary


def main() -> None:
    tested_model_path = "checkpoints/versioned/A4.pt"
    A3_model_path = "checkpoints/versioned/A3.pt"

    print("========== Part 1: A4 vs random ==========")
    A4_vs_random = evaluate_actor_critic_vs_random_balanced(
        checkpoint_path=tested_model_path,
        n_games_per_color=20,
        max_steps=300,
        greedy=True,
        device="cpu",
    )
    print(f"A4 vs random total_games = {A4_vs_random['total_games']}")
    print(f"A4 win = {A4_vs_random['model_win']}")
    print(f"random win = {A4_vs_random['random_win']}")
    print(f"draw = {A4_vs_random['draw']}")
    print(f"A4 win rate = {A4_vs_random['model_win_rate']:.2%}")
    print(f"avg_steps = {A4_vs_random['avg_steps']:.2f}")
    print(
        f"step_limit = "
        f"{A4_vs_random['reached_step_limit_count']}/{A4_vs_random['total_games']} "
        f"({A4_vs_random['step_limit_rate']:.2%})"
    )
    print()

    print("========== Part 2: A4 vs A3 final model ==========")
    A4_vs_A3 = evaluate_model_vs_model_balanced(
        tested_model_path=tested_model_path,
        opponent_model_path=A3_model_path,
        tested_model_name="A4",
        opponent_model_name="A3",
        n_games_per_color=20,
        max_steps=300,
        greedy=True,
        device="cpu",
    )
    print(f"A4 vs A3 total_games = {A4_vs_A3['total_games']}")
    print(f"A4 win = {A4_vs_A3['tested_model_win']}")
    print(f"A3 win = {A4_vs_A3['opponent_win']}")
    print(f"draw = {A4_vs_A3['draw']}")
    print(f"A4 win rate = {A4_vs_A3['tested_model_win_rate']:.2%}")
    print(f"avg_steps = {A4_vs_A3['avg_steps']:.2f}")
    print(
        f"step_limit = "
        f"{A4_vs_A3['reached_step_limit_count']}/{A4_vs_A3['total_games']} "
        f"({A4_vs_A3['step_limit_rate']:.2%})"
    )

    save_json(
        A4_vs_random,
        "eval_logs/A4_vs_random.json",
    )
    save_json(
        A4_vs_A3,
        "eval_logs/A4_vs_A3.json",
    )

    print()
    print("详细结果已保存到：")
    print("  eval_logs/A4_vs_random.json")
    print("  eval_logs/A4_vs_A3.json")


if __name__ == "__main__":
    main()