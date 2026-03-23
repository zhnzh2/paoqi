from game import Game


def print_help() -> None:
    print("可用命令：")
    print("  move x y       在落子阶段，对 (x, y) 执行统一落子操作")
    print("                 - 若该格为空，则尝试放置1级己方棋子")
    print("                 - 若该格有己方1/2级棋子，则尝试升级")
    print("                 - 其他情况报错")
    print("  cannon i dir   为第 i 门新炮指定炮口方向（dir: left/right/up/down）")
    print("  capturable     显示当前可吃目标")
    print("  eat i          吃掉第 i 个可吃目标")
    print("  fireable       显示当前可发射的炮")
    print("  fire i         发射第 i 门可发射炮")
    print("  undo           撤销上一次主动操作（可连续多次）")
    print("  record         显示正式棋谱")
    print("  debug          显示调试日志")
    print("  end            结束当前回合，轮到对方")
    print("  show           重新显示棋盘")
    print("  legal          显示当前所有合法落子操作")
    print("  cannons        显示当前棋盘上的所有炮管")
    print("  history        显示正式棋谱（与 record 相同）")
    print("  help           显示帮助")
    print("  quit           退出程序")


def main() -> None:
    game = Game()

    print("欢迎来到 炮棋 v0.7！")
    print("当前版本实现：基本落子/升级规则，炮管扫描，炮口选择，打炮、吃子与双方连锁结算。")
    print("当前版本支持正式棋谱记录，以及对落子、选炮口、打炮、吃子等操作进行连续撤销。")
    print_help()
    print()

    while True:
        if game.check_game_over_at_turn_start():
            print(game.board.render())
            print()
            print(game.game_result_report())
            break

        print(game.board.render())
        print()
        print(game.status_text())
        print()

        print(game.phase_name())
        
        if game.phase == "fire":
            print(game.fireable_report())
        elif game.phase == "eat":
            print(game.capturable_report())
        elif game.phase == "muzzle":
            print(game.pending_muzzle_report())
            
        command = input("请输入命令 > ").strip()

        if not command:
            print("请输入有效命令。")
            print()
            continue

        lowered = command.lower()

        # 有待选炮口时，禁止 move / fire / end
        if game.has_pending_muzzle_choice():
            if not (
                lowered.startswith("cannon ")
                or lowered in {
                    "help",
                    "history",
                    "record",
                    "debug",
                    "cannons",
                    "show",
                    "undo",
                    "quit",
                }
            ):
                print("当前有新炮尚未确定炮口方向，请先使用 cannon i dir。")
                print(game.pending_muzzle_report())
                print()
                continue

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
            print("当前所有合法落子操作：")
            if not legal_moves:
                print("  （无）")
            else:
                for move in legal_moves:
                    print(" ", move)
            print()
            continue

        if lowered == "cannons":
            print(game.cannon_report())
            print()
            continue

        if lowered == "history":
            print(game.history_text())
            print()
            continue

        if lowered == "record":
            print(game.history_text())
            print()
            continue

        if lowered == "debug":
            print("调试日志：")
            if not game.debug_log:
                print("  （暂无）")
            else:
                for i, item in enumerate(game.debug_log, start=1):
                    print(f"  {i}. {item}")
            print()
            continue

        if lowered == "undo":
            try:
                game.undo()
                print("已撤销上一次操作。")
                print()

            except ValueError as e:
                print(f"撤销失败：{e}")
                print()

            continue

        if lowered.startswith("cannon "):
            parts = command.split()
            if len(parts) != 3:
                print("命令格式错误。请使用：cannon 编号 方向")
                print()
                continue

            try:
                idx = int(parts[1])
                dir_text = parts[2]

                game.set_cannon_mouth(idx, dir_text)
                print("炮口方向设置成功。")

                if game.phase == "muzzle":
                    print(game.pending_muzzle_report())
                elif game.phase == "fire":
                    print("已进入打炮阶段。")
                    print(game.fireable_report())
                elif game.phase == "eat":
                    print("已进入吃子阶段。")
                    print(game.capturable_report())
                elif game.phase == "drop":
                    print("当前大回合已结束，已切换到下一名玩家的落子阶段。")

                print()

            except ValueError as e:
                print(f"操作失败：{e}")
                print()

            continue

        if lowered == "fireable":
            print(game.fireable_report())
            print()
            continue

        if lowered == "capturable":
            print(game.capturable_report())
            print()
            continue

        if lowered.startswith("eat "):
            parts = command.split()
            if len(parts) != 2:
                print("命令格式错误。请使用：eat 编号")
                print()
                continue

            try:
                idx = int(parts[1])

                game.eat_target_by_index(idx)
                print("吃子成功。")
                print(game.new_cannons_report())

                if game.has_pending_muzzle_choice():
                    print(game.pending_muzzle_report())
                elif game.phase == "fire":
                    print("已返回打炮阶段。")
                    print(game.fireable_report())
                else:
                    print(game.capturable_report())

                print()

            except ValueError as e:
                print(f"操作失败：{e}")
                print()

            continue

        if lowered.startswith("fire "):
            parts = command.split()
            if len(parts) != 2:
                print("命令格式错误。请使用：fire 编号")
                print()
                continue

            try:
                idx = int(parts[1])

                game.fire_cannon_by_index(idx)
                print("发炮成功。")
                print(game.fire_report_text())

                if game.has_pending_muzzle_choice():
                    print(game.pending_muzzle_report())
                else:
                    print(game.fireable_report())

                print()

            except ValueError as e:
                print(f"操作失败：{e}")
                print()

            continue

        if lowered == "end":
            if game.phase == "drop":
                print("当前还是落子阶段，不能直接结束回合。请先执行一次 move。")
                print()
                continue

            if game.phase == "muzzle":
                print("当前还有新炮未确定炮口，不能结束回合。")
                print(game.pending_muzzle_report())
                print()
                continue

            game.end_turn()
            print("回合结束，已切换到对方。")
            print()
            continue

        if game.phase != "drop":
            print("当前阶段不接受该命令。")
            if game.phase == "muzzle":
                print("你现在需要先为新炮指定炮口方向：cannon i dir")
                print(game.pending_muzzle_report())
            elif game.phase == "fire":
                print("你现在处于打炮阶段，可使用：fireable / fire i / end")
            elif game.phase == "eat":
                print("你现在处于吃子阶段，可使用：capturable / eat i / end")
            print()
            continue

        try:
            game.apply_command(command)
            print("操作成功。")
            print(game.new_cannons_report())

            if game.has_pending_muzzle_choice():
                print(game.pending_muzzle_report())
            else:
                print("已进入打炮阶段。")
                print(game.fireable_report())

            print()

        except ValueError as e:
            print(f"操作失败：{e}")
            print()


if __name__ == "__main__":
    main()