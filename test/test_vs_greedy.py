#test_vs_greedy.py
from core.game import Game
from core.AI import AlphaBetaAgent, GreedyAgent
from tools.match_io import save_match_result

def encode_board_numeric(game: Game) -> list[list[int]]:
    rows = []
    for y in range(1, 10):
        row = []
        for x in range(1, 10):
            piece = game.board.get(x, y)
            if piece is None:
                row.append(0)
            elif piece.color == "R":
                row.append(piece.level)
            else:
                row.append(-piece.level)
        rows.append(row)
    return rows

def encode_board_compact(game: Game) -> list[list[str]]:
    rows = []
    for y in range(1, 10):
        row = []
        for x in range(1, 10):
            piece = game.board.get(x, y)
            if piece is None:
                row.append(".")
            else:
                row.append(f"{piece.color}{piece.level}")
        rows.append(row)
    return rows

def run_one_game(red_depth: int = 2, max_steps: int = 300):
    game = Game()

    red_agent = AlphaBetaAgent(color="R", depth=red_depth, verbose=True)
    blue_agent = GreedyAgent(color="B", verbose=False)

    step = 0
    action_log = []
    state_log = []

    while not game.is_terminal() and step < max_steps:
        if game.current_player == "R":
            agent = red_agent
        else:
            agent = blue_agent

        action = agent.choose_action(game)
        if action is None:
            print("没有合法动作，测试终止。")
            break

        state_log.append(
            {
                "step": step + 1,
                "player": game.current_player,
                "phase": game.phase,
                "board": encode_board_compact(game),
                "board_numeric": encode_board_numeric(game),
            }
        )

        action_log.append(
            {
                "step": step + 1,
                "player": game.current_player,
                "action": action,
            }
        )

        game.apply_action(action)
        step += 1

    reached_step_limit = (not game.is_terminal() and step >= max_steps)

    if reached_step_limit:
        winner = game.determine_winner_by_score()
    else:
        winner = game.get_winner()

    red_score, blue_score = game.calculate_score()

    training_samples = []
    for action_item, state_item in zip(action_log, state_log):
        player = action_item["player"]
        training_samples.append(
            {
                "step": action_item["step"],
                "player": player,
                "phase": state_item["phase"],
                "board": state_item["board"],
                "board_numeric": state_item["board_numeric"],
                "action": action_item["action"],
                "winner": winner,
                "is_winner_move": (winner is not None and player == winner),
            }
        )

    return {
        "winner": winner,
        "steps": step,
        "terminal": game.is_terminal(),
        "reached_step_limit": reached_step_limit,
        "red_score": red_score,
        "blue_score": blue_score,
        "final_board": game.board.render(),
        "history_text": game.history_text(),
        "action_log": action_log,
        "training_samples": training_samples,
    }


def run_series(n: int = 20, red_depth: int = 2, max_steps: int = 300):
    red_win = 0
    blue_win = 0
    draw = 0

    for i in range(n):
        result = run_one_game(red_depth=red_depth, max_steps=max_steps)
        winner = result["winner"]

        if winner == "R":
            red_win += 1
        elif winner == "B":
            blue_win += 1
        else:
            draw += 1

        print(
            f"第{i + 1}局：winner={winner}, "
            f"steps={result['steps']}, terminal={result['terminal']}, "
            f"step_limit={result['reached_step_limit']}, "
            f"score=({result['red_score']}, {result['blue_score']})"
        )
        print(result["final_board"])

        saved_path = save_match_result(
            result={
                "mode": "ai_vs_greedy",
                "red_depth": red_depth,
                "game_index": i + 1,
                **result,
            },
            folder="match_logs/ai_vs_greedy",
            prefix="ai_vs_greedy",
        )
        print(f"已保存：{saved_path}")
        print()

    print("统计结果：")
    print(f"总局数：{n}")
    print(f"红方 AlphaBeta(depth={red_depth}) 胜：{red_win}")
    print(f"蓝方 Greedy 胜：{blue_win}")
    print(f"平局/未分胜负：{draw}")
    print(f"红方胜率：{red_win / n:.2%}")
    print(f"蓝方胜率：{blue_win / n:.2%}")


if __name__ == "__main__":
    run_series(n=3, red_depth=3, max_steps=300)