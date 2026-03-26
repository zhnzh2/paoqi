#record.py
from __future__ import annotations

from typing import List

from core.board import Position
from core.models import Cannon


def player_name(color: str) -> str:
    return "红方" if color == "R" else "蓝方"


def format_pos(pos: Position) -> str:
    x, y = pos
    return f"({x}, {y})"


def mouth_text(mouth: str) -> str:
    mapping = {
        "L": "左",
        "R": "右",
        "U": "上",
        "D": "下",
    }
    return mapping.get(mouth, mouth)


def cannon_direction_text(direction: str) -> str:
    mapping = {
        "H": "横",
        "V": "纵",
    }
    return mapping.get(direction, direction)

def format_cannon_positions_for_record(cannon: Cannon) -> str:
    pos_texts = [format_pos(pos) for pos in cannon.positions]
    return "[" + ", ".join(pos_texts) + "]"


def format_cannon_tuple_record(cannon: Cannon) -> str:
    k = cannon.level
    n = len(cannon.positions)
    a_text = format_cannon_positions_for_record(cannon)
    dir_text = cannon_direction_text(cannon.direction)

    if cannon.mouth is None:
        mouth_name = "未定口"
    else:
        mouth_name = mouth_text(cannon.mouth)

    return f"({k}, {n}, {a_text}, {dir_text}, {mouth_name})"


def format_cannon_for_record(cannon: Cannon, style: int) -> str:
    if style == 1:
        return cannon.short()

    if style == 2:
        return format_cannon_tuple_record(cannon)

    return cannon.short()


def format_cannon_with_mouth_for_record(cannon: Cannon, style: int) -> str:
    base = format_cannon_for_record(cannon, style)

    if cannon.mouth is None:
        return base

    if style == 2:
        return base

    return f"{base}（{mouth_text(cannon.mouth)}口）"

def history_text(history: List[str]) -> str:
    if not history:
        return "当前还没有正式棋谱。"

    lines: List[str] = ["正式棋谱："]
    for i, item in enumerate(history, start=1):
        lines.append(f"  {i}. {item}")
    return "\n".join(lines)


def debug_text(debug_log: List[str]) -> str:
    if not debug_log:
        return "当前还没有调试日志。"

    lines: List[str] = ["调试日志："]
    for i, item in enumerate(debug_log, start=1):
        lines.append(f"  {i}. {item}")
    return "\n".join(lines)


def fire_report_text(last_fire_report_lines: List[str]) -> str:
    if not last_fire_report_lines:
        return "本次没有发炮明细。"
    return "\n".join(last_fire_report_lines)

def piece_text(piece) -> str:
    if piece is None:
        return "空"
    return piece.short()

def new_cannons_report(cannons: List[Cannon]) -> str:
    if not cannons:
        return "本步未形成新炮。"

    lines: List[str] = ["新形成炮管："]

    for cannon in cannons:
        lines.append(f"  {player_name(cannon.color)} {cannon.short()}")

    return "\n".join(lines)

def pending_muzzle_report(cannons: List[Cannon]) -> str:
    if not cannons:
        return "当前没有待选择炮口的新炮。"

    lines: List[str] = ["请为新炮选择炮口方向："]

    for i, cannon in enumerate(cannons, start=1):
        if cannon.direction == "H":
            hint = "left / right"
        else:
            hint = "up / down"

        lines.append(
            f"  {i}. {player_name(cannon.color)} {cannon.short()}  -> 可选: {hint}"
        )

    return "\n".join(lines)

def fireable_report(player_color: str, cannons: List[Cannon]) -> str:
    lines: List[str] = []
    lines.append(f"{player_name(player_color)} 当前可发射炮管：")

    if not cannons:
        lines.append("  （暂无）")
    else:
        for i, cannon in enumerate(cannons, start=1):
            lines.append(f"  {i}. {cannon.short()}")

    return "\n".join(lines)

def capturable_report(player_color: str, targets: List[tuple[int, int]], board) -> str:
    lines: List[str] = []
    lines.append(f"{player_name(player_color)} 当前可吃目标：")

    if not targets:
        lines.append("  （暂无）")
    else:
        for i, (x, y) in enumerate(targets, start=1):
            piece = board.get(x, y)
            if piece is not None:
                lines.append(f"  {i}. ({x}, {y}) {piece.short()}")

    return "\n".join(lines)

def cannon_report(red_cannons: List[Cannon], blue_cannons: List[Cannon]) -> str:
    lines: List[str] = []

    lines.append("红方炮管：")
    if not red_cannons:
        lines.append("  （暂无）")
    else:
        for i, cannon in enumerate(red_cannons, start=1):
            lines.append(f"  {i}. {cannon.short()}")

    lines.append("")
    lines.append("蓝方炮管：")

    if not blue_cannons:
        lines.append("  （暂无）")
    else:
        for i, cannon in enumerate(blue_cannons, start=1):
            lines.append(f"  {i}. {cannon.short()}")

    return "\n".join(lines)