#test_series.py
from core.game import Game
from core.AI import AlphaBetaAgent, RandomAgent


def run_one_game(red_depth: int = 2, max_steps: int = 300):
    game = Game()

    red_agent = AlphaBetaAgent(color="R", depth=red_depth)
    blue_agent = RandomAgent(color="B")

    step = 0

    while not game.is_terminal() and step < max_steps:
        if game.current_player == "R":
            agent = red_agent
        else:
            agent = blue_agent

        action = agent.choose_action(game)
        if action is None:
            break

        game.apply_action(action)
        step += 1

    return {
        "winner": game.get_winner(),
        "steps": step,
        "terminal": game.is_terminal(),
        "final_board": game.board.render(),
    }


def run_series(n: int, red_depth: int, max_steps: int = 300):
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
            f"steps={result['steps']}, terminal={result['terminal']}"
        )
        print(result["final_board"])
        print()

    print("\n统计结果：")
    print(f"总局数：{n}")
    print(f"红方AI胜：{red_win}")
    print(f"蓝方随机胜：{blue_win}")
    print(f"平局/未分胜负：{draw}")
    print(f"红方AI胜率：{red_win / n:.2%}")


if __name__ == "__main__":
    run_series(n=100, red_depth=2, max_steps=300)