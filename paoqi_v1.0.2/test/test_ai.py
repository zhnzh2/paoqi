from game import Game
from AI import AlphaBetaAgent


def test_choose_action():
    game = Game()
    agent = AlphaBetaAgent(color=game.current_player, depth=2)

    action = agent.choose_action(game)

    print("当前玩家：", game.current_player)
    print("AI 选择动作：", action)


if __name__ == "__main__":
    test_choose_action()