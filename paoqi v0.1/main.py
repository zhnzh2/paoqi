from game import Game


def print_help() -> None:
    print("可用命令：")
    print("  move x y       对 (x, y) 执行统一落子操作")
    print("                 - 若该格为空，则尝试放置1级己方棋子")
    print("                 - 若该格有己方1/2级棋子，则尝试升级")
    print("                 - 其他情况报错")
    print("  show           重新显示棋盘")
    print("  legal          显示当前所有合法操作")
    print("  history        显示历史记录")
    print("  help           显示帮助")
    print("  quit           退出程序")


def main() -> None:
    game = Game()

    print("欢迎来到 炮棋 V0（命令行本地双人版）")
    print("当前版本仅实现：初始布局、统一落子、无法落子判负。")
    print_help()
    print()

    while True:
        if game.check_game_over_at_turn_start():
            print(game.board.render())
            print()
            loser = game.player_name(game.current_player)
            winner = game.player_name(game.winner) if game.winner else "未知"
            print(f"{loser} 无法进行任何合法落子操作，游戏结束。")
            print(f"胜者：{winner}")
            break

        print(game.board.render())
        print()
        print(game.status_text())
        print()

        command = input("请输入命令 > ").strip()

        if not command:
            print("请输入有效命令。")
            print()
            continue

        lowered = command.lower()

        if lowered == "quit":
            print("已退出游戏。")
            break
        if lowered == "help":
            print_help()
            print()
            continue
        if lowered == "show":
            print()
            continue
        if lowered == "legal":
            legal_moves = game.all_legal_moves(game.current_player)
            print("当前所有合法操作：")
            if not legal_moves:
                print("  （无）")
            else:
                for move in legal_moves:
                    print(" ", move)
            print()
            continue
        if lowered == "history":
            print("历史记录：")
            if not game.history:
                print("  （暂无）")
            else:
                for item in game.history:
                    print(" ", item)
            print()
            continue

        try:
            game.apply_command(command)
            print("操作成功。")
            print()
            game.end_turn()
        except ValueError as e:
            print(f"操作失败：{e}")
            print()


if __name__ == "__main__":
    main()