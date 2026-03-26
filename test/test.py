from game import Game

g = Game()

print(g.get_legal_actions_snapshot())

action = g.get_legal_actions()[0]
print("准备执行：", action)

g.apply_action(action)

print(g.get_state_snapshot()["phase_info"])
print(g.get_legal_actions_snapshot())