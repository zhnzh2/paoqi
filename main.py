#main.py
import json
from core.game import Game

def print_help() -> None:
    print("可用命令：")
    print("  x y            在落子阶段，对 (x, y) 执行统一落子操作")
    print("                 - 若该格为空，则尝试放置1级己方棋子")
    print("                 - 若该格有己方1/2级棋子，则尝试升级")
    print("  i              在打炮阶段，发射第 i 门可发射炮")
    print("                 在吃子阶段，吃掉第 i 个可吃目标")
    print("  i dir          在选炮口阶段，为第 i 门新炮指定方向")
    print("                 dir: left/right/up/down")
    print("  move x y       也可继续使用完整落子命令")
    print("  fire i         也可继续使用完整打炮命令")
    print("  eat i          也可继续使用完整吃子命令")
    print("  cannon i dir   也可继续使用完整选炮口命令")
    print("  ops            按行显示从开局到现在的所有操作记录")
    print("  capturable     显示当前可吃目标")
    print("  fireable       显示当前可发射的炮")
    print("  undo           撤销上一次主动操作（可连续多次）")
    print("  record         显示正式棋谱")
    print("  debug          显示调试日志")
    print("  end            结束当前回合，轮到对方")
    print("  show           重新显示棋盘")
    print("  legal          显示当前所有合法动作")
    print("  cannons        显示当前棋盘上的所有炮管")
    print("  history        显示正式棋谱（与 record 相同）")
    print("  events         显示最近一次主动动作的结构化事件")
    print("  help           显示帮助")
    print("  save 文件名     将当前对局保存为 JSON 存档")
    print("  load 文件名     从 JSON 存档读取对局")
    print("                 建议文件名使用 .json 后缀")
    print("  quit           退出程序")

def parse_input_to_action(game: Game, text: str) -> dict | None:
    raw = text.strip()
    if not raw:
        return None

    parts = raw.split()
    head = parts[0].lower()

    # move x y
    if head == "move":
        if len(parts) != 3:
            raise ValueError("move 命令格式错误，应为：move x y")
        x = int(parts[1])
        y = int(parts[2])

        piece = game.board.get(x, y)
        if piece is None:
            return {
                "type": "move",
                "mode": "place",
                "x": x,
                "y": y,
            }

        return {
            "type": "move",
            "mode": "upgrade",
            "x": x,
            "y": y,
        }

    # 直接输入 x y
    if len(parts) == 2:
        try:
            x = int(parts[0])
            y = int(parts[1])
        except ValueError:
            pass
        else:
            piece = game.board.get(x, y)
            if piece is None:
                return {
                    "type": "move",
                    "mode": "place",
                    "x": x,
                    "y": y,
                }

            return {
                "type": "move",
                "mode": "upgrade",
                "x": x,
                "y": y,
            }

    # 选炮口阶段：若只输入方向，默认作用于第 1 门待选新炮
    if len(parts) == 1 and parts[0].lower() in {"left", "right", "up", "down"}:
        if game.phase == "muzzle":
            return {
                "type": "muzzle",
                "index": 1,
                "direction": parts[0].lower(),
            }

    # cannon i dir
    if head == "cannon":
        if len(parts) != 3:
            raise ValueError("cannon 命令格式错误，应为：cannon i direction")
        return {
            "type": "muzzle",
            "index": int(parts[1]),
            "direction": parts[2].lower(),
        }

    # 直接输入 i dir
    if len(parts) == 2 and parts[1].lower() in {"left", "right", "up", "down"}:
        try:
            index = int(parts[0])
        except ValueError:
            pass
        else:
            return {
                "type": "muzzle",
                "index": index,
                "direction": parts[1].lower(),
            }

    # fire i
    if head == "fire":
        if len(parts) != 2:
            raise ValueError("fire 命令格式错误，应为：fire i")
        return {
            "type": "fire",
            "index": int(parts[1]),
        }

    # eat i
    if head == "eat":
        if len(parts) != 2:
            raise ValueError("eat 命令格式错误，应为：eat i")
        return {
            "type": "eat",
            "index": int(parts[1]),
        }

    # 单个整数：在当前阶段解释
    if len(parts) == 1:
        try:
            index = int(parts[0])
        except ValueError:
            pass
        else:
            if game.phase == "fire":
                return {
                    "type": "fire",
                    "index": index,
                }
            if game.phase == "eat":
                return {
                    "type": "eat",
                    "index": index,
                }

    return None

def save_game_to_file(game: Game, filename: str) -> None:
    data = game.export_full_state()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game_from_file(filename: str) -> Game:
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Game.from_exported_state(data)

def print_phase_prompt(game: Game) -> None:
    print(game.phase_name())

    if game.phase == "fire":
        print(game.fireable_report())
    elif game.phase == "eat":
        print(game.capturable_report())
    elif game.phase == "muzzle":
        print(game.pending_muzzle_report())

def print_action_events(result: dict) -> None:
    payload = result.get("result")
    if not payload:
        return

    events = payload.get("events", [])
    if not events:
        return

    print("本次结构化事件：")
    for event in events:
        event_type = event.get("type")

        if event_type == "piece_change":
            x = event["x"]
            y = event["y"]
            reason = event.get("reason", "")
            before = event.get("before")
            after = event.get("after")
            print(f"  piece_change @ ({x}, {y}) [{reason}] : {before} -> {after}")
            continue

        if event_type == "new_cannon":
            cannon = event.get("cannon")
            print(f"  new_cannon : {cannon}")
            continue

        if event_type == "muzzle_set":
            print(
                f"  muzzle_set : index={event.get('index')} "
                f"direction={event.get('direction')} "
                f"cannon={event.get('cannon')}"
            )
            continue

        if event_type == "fire":
            print(
                f"  fire : index={event.get('index')} "
                f"player={event.get('player')} "
                f"cannon={event.get('cannon')}"
            )
            continue

        if event_type == "capture":
            print(
                f"  capture @ ({event.get('x')}, {event.get('y')}) : "
                f"{event.get('captured')} -> {event.get('placed')}"
            )
            continue

        if event_type == "phase_change":
            print(
                f"  phase_change : {event.get('current_player_name', event.get('current_player'))} "
                f"-> {event.get('phase_name', event.get('phase'))}"
            )
            continue

        if event_type == "turn_change":
            print(
                f"  turn_change : turn={event.get('turn_number')} "
                f"player={event.get('current_player_name', event.get('current_player'))} "
                f"reason={event.get('reason')}"
            )
            continue

        if event_type == "auto_action":
            print(
                f"  auto_action : {event.get('action_type')} "
                f"reason={event.get('reason')}"
            )
            continue

        print(f"  {event_type} : {event}")

def print_post_action_feedback(game: Game) -> None:
    auto_messages = game.consume_auto_action_messages()
    if auto_messages:
        for msg in auto_messages:
            print(msg)
    else:
        if game.phase == "muzzle":
            print(game.new_cannons_report())
        elif game.phase == "fire":
            print(game.fire_report_text())
        elif game.phase == "eat":
            print(game.capturable_report())

    if game.has_pending_muzzle_choice():
        print(game.pending_muzzle_report())
    elif game.phase == "fire":
        print(game.fireable_report())
    elif game.phase == "eat":
        print(game.capturable_report())
    elif game.phase == "drop":
        print("当前大回合已结束，已切换到下一名玩家的落子阶段。")

def print_post_action_feedback_from_result(game: Game, result: dict) -> None:
    payload = result.get("result")
    if not payload:
        return

    print(f"标准动作：{payload.get('action_text')}")

    print_action_events(result)

    auto_messages = payload.get("auto_action_messages", [])
    if auto_messages:
        print("自动结算提示：")
        for msg in auto_messages:
            print(msg)

    after = payload.get("after", {})
    phase_info = after.get("phase_info", {})
    legal_info = after.get("legal_actions", {})

    print("执行后状态：")
    print(
        f"  当前行动方：{phase_info.get('current_player_name')} | "
        f"当前阶段：{phase_info.get('phase_name')} | "
        f"合法动作数：{legal_info.get('count')}"
    )

    if game.has_pending_muzzle_choice():
        print(game.pending_muzzle_report())
    elif game.phase == "fire":
        print(game.fireable_report())
    elif game.phase == "eat":
        print(game.capturable_report())
    elif game.phase == "drop":
        print("当前大回合已结束，已切换到下一名玩家的落子阶段。")


def main() -> None:
    game = Game()

    print("欢迎来到 炮棋 v1.0.0！")
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

        auto_messages = game.consume_auto_action_messages()
        for msg in auto_messages:
            print(msg)
        if auto_messages:
            print()

        print_phase_prompt(game)

        command = input("请输入命令 > ").strip()

        if not command:
            print("请输入有效命令。")
            print()
            continue

        lowered = command.lower()

        # 系统命令
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
            legal_info = game.get_legal_actions_snapshot()
            print("当前所有合法动作：")
            print(
                f"  当前阶段：{legal_info['phase']} | "
                f"行动方：{legal_info['current_player']} | "
                f"动作数：{legal_info['count']}"
            )
            if legal_info["count"] == 0:
                print("  （无）")
            else:
                for action in legal_info["actions"]:
                    print(" ", action["label"])
            print()
            continue

        if lowered == "cannons":
            print(game.cannon_report())
            print()
            continue

        if lowered == "ops":
            print(game.command_log_text())
            print()
            continue

        if lowered == "history":
            print(game.history_text())
            print()
            continue

        if lowered == "events":
            events = game.get_last_action_events()
            print("最近一次主动动作的结构化事件：")
            if not events:
                print("  （暂无）")
            else:
                for event in events:
                    print(" ", event)
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
                game.log_command("undo")
                print("已撤销上一次操作。")
                print()
            except ValueError as e:
                print(f"撤销失败：{e}")
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

        if lowered.startswith("save "):
            filename = command[5:].strip()
            if not filename:
                print("保存失败：请提供文件名。")
                print()
                continue

            try:
                save_game_to_file(game, filename)
                print(f"已保存到：{filename}")
                print()
            except Exception as e:
                print(f"保存失败：{e}")
                print()
            continue

        if lowered.startswith("load "):
            filename = command[5:].strip()
            if not filename:
                print("读档失败：请提供文件名。")
                print()
                continue

            try:
                game = load_game_from_file(filename)
                print(f"已从存档读取：{filename}")
                print()
            except Exception as e:
                print(f"读档失败：{e}")
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

        # 尝试解析为结构化动作
        try:
            action = parse_input_to_action(game, command)
        except ValueError as e:
            print(f"命令解析失败：{e}")
            print()
            continue

        if action is None:
            print("未知命令。输入 help 查看可用命令。")
            print()
            continue

        result = game.try_apply_action_with_snapshot(action)
        if not result["ok"]:
            print(f"操作失败：{result['message']}")
            print()
            continue

        standardized = game.action_to_command_text(action)
        game.log_command(standardized)

        print("操作成功。")
        print_post_action_feedback_from_result(game, result)
        print()

if __name__ == "__main__":
    main()