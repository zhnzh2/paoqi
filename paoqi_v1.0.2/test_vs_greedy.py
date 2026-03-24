from game import Game
from AI import AlphaBetaAgent, GreedyAgent


def run_one_game(red_depth: int = 2, max_steps: int = 300):
    game = Game()

    red_agent = AlphaBetaAgent(color="R", depth=red_depth, verbose=False)
    blue_agent = GreedyAgent(color="B", verbose=False)

    step = 0

    while not game.is_terminal() and step < max_steps:
        if game.current_player == "R":
            agent = red_agent
        else:
            agent = blue_agent

        action = agent.choose_action(game)
        if action is None:
            print("没有合法动作，测试终止。")
            break

        game.apply_action(action)
        step += 1

    reached_step_limit = (not game.is_terminal() and step >= max_steps)

    if reached_step_limit:
        winner = game.determine_winner_by_score()
    else:
        winner = game.get_winner()

    return {
        "winner": winner,
        "steps": step,
        "terminal": game.is_terminal(),
        "reached_step_limit": reached_step_limit,
        "final_board": game.board.render(),
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
            f"step_limit={result['reached_step_limit']}"
        )
        print(result["final_board"])
        print()

    print("统计结果：")
    print(f"总局数：{n}")
    print(f"红方 AlphaBeta(depth={red_depth}) 胜：{red_win}")
    print(f"蓝方 Greedy 胜：{blue_win}")
    print(f"平局/未分胜负：{draw}")
    print(f"红方胜率：{red_win / n:.2%}")
    print(f"蓝方胜率：{blue_win / n:.2%}")


if __name__ == "__main__":
    run_series(n=20, red_depth=3, max_steps=300)