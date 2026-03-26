from rl.train_actor_critic import save_actor_critic_model, train_actor_critic_selfplay


def main() -> None:
    model, history = train_actor_critic_selfplay(
        iterations=100,
        episodes_per_iteration=20,
        max_steps=300,
        learning_rate=1e-4,
        value_coef=0.5,
        entropy_coef=0.005,
        save_every=20,
        checkpoint_dir="checkpoints/actor_critic_pool",
        random_opponent_prob=0.3,
        current_opponent_prob=0.4,
        history_save_dir="logs/actor_critic_histories",
        history_json_path="logs/actor_critic_history.json",
        device="cpu",
    )

    save_actor_critic_model(
        model,
        "checkpoints/actor_critic_pool/final_model.pt",
    )

    print("训练完成。")
    print(f"history length = {len(history)}")
    print("最终模型已保存到 checkpoints/actor_critic_pool/final_model.pt")


if __name__ == "__main__":
    main()