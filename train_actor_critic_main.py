from rl.train_actor_critic import save_actor_critic_model, train_actor_critic_selfplay


def main() -> None:
    model, history = train_actor_critic_selfplay(
        iterations=10,
        episodes_per_iteration=20,
        max_steps=300,
        learning_rate=1e-4,
        value_coef=0.5,
        entropy_coef=0.005,
        save_every=5,
        checkpoint_dir="checkpoints/versioned/A4_rl_checkpoints",
        random_opponent_prob=0.3,
        current_opponent_prob=0.4,
        history_save_dir="logs/A4_rl_histories",
        history_json_path="logs/A4_rl_history.json",
        initial_model_path="checkpoints/versioned/A3.pt",
        device="cpu",
    )

    save_actor_critic_model(
        model,
        "checkpoints/versioned/A4.pt",
    )

    print("训练完成。")
    print(f"history length = {len(history)}")
    print("最终模型已保存到 checkpoints/versioned/A4.pt")


if __name__ == "__main__":
    main()