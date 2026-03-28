from rl.human_vs_model_recorder import run_human_vs_model_game


def main() -> None:
    checkpoint_path = "checkpoints/versioned/A3.pt"

    run_human_vs_model_game(
        checkpoint_path=checkpoint_path,
        human_color="B",
        max_steps=300,
        greedy=True,
        device="cpu",
        output_folder="human_game_logs",
    )


if __name__ == "__main__":
    main()