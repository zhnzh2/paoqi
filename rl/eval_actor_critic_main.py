from rl.eval_actor_critic import (
    evaluate_actor_critic_vs_random_balanced,
    save_json,
)


def main() -> None:
    checkpoint_path = "checkpoints/actor_critic_pool/final_model.pt"

    result = evaluate_actor_critic_vs_random_balanced(
        checkpoint_path=checkpoint_path,
        n_games_per_color=20,
        max_steps=300,
        greedy=True,
        device="cpu",
    )

    print("评测完成。")
    print(f"checkpoint = {checkpoint_path}")
    print(f"total_games = {result['total_games']}")
    print(f"model_win = {result['model_win']}")
    print(f"random_win = {result['random_win']}")
    print(f"draw = {result['draw']}")
    print(f"model_win_rate = {result['model_win_rate']:.2%}")
    print(f"random_win_rate = {result['random_win_rate']:.2%}")
    print(f"draw_rate = {result['draw_rate']:.2%}")
    print(f"avg_steps = {result['avg_steps']:.2f}")
    print(
        f"step_limit = "
        f"{result['reached_step_limit_count']}/{result['total_games']} "
        f"({result['step_limit_rate']:.2%})"
    )

    print()
    print("红方执子评测：")
    print(
        f"  model_win_rate = "
        f"{result['red_side_summary']['model_win_rate']:.2%}, "
        f"avg_steps = {result['red_side_summary']['avg_steps']:.2f}"
    )

    print("蓝方执子评测：")
    print(
        f"  model_win_rate = "
        f"{result['blue_side_summary']['model_win_rate']:.2%}, "
        f"avg_steps = {result['blue_side_summary']['avg_steps']:.2f}"
    )

    save_json(
        result,
        "eval_logs/actor_critic_vs_random_balanced.json",
    )
    print("详细结果已保存到 eval_logs/actor_critic_vs_random_balanced.json")


if __name__ == "__main__":
    main()