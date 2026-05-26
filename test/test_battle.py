from core.game import Game
from core.AI import AlphaBetaAgent, RandomAgent


def run_ai_vs_random(max_steps: int = 1000):
    game = Game()

    red_agent = AlphaBetaAgent(color="R", depth=2, verbose=True)
    blue_agent = RandomAgent(color="B")

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

        print(f"Step {step + 1}: 玩家 {game.current_player} 选择 {action}")

        game.apply_action(action)
        step += 1

    print("\n对局结束")
    print("总步数：", step)
    print("是否终局：", game.is_terminal())
    print("胜者：", game.get_winner())
    print(game.board.render())
    print(game.history_text())


if __name__ == "__main__":
    run_ai_vs_random()