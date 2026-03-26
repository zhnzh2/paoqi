#action_codec.py
from __future__ import annotations

from typing import Any

from core.game import Game


BOARD_SIZE = 9
BOARD_CELLS = BOARD_SIZE * BOARD_SIZE


def pos_to_index(x: int, y: int) -> int:
    return (y - 1) * BOARD_SIZE + (x - 1)


def index_to_pos(index: int) -> tuple[int, int]:
    x = (index % BOARD_SIZE) + 1
    y = (index // BOARD_SIZE) + 1
    return x, y


def build_all_cannon_segments() -> list[tuple[tuple[int, int], ...]]:
    segments: list[tuple[tuple[int, int], ...]] = []

    # 横向线段
    for y in range(1, BOARD_SIZE + 1):
        for length in range(3, BOARD_SIZE + 1):
            for start_x in range(1, BOARD_SIZE - length + 2):
                segment = tuple(
                    (start_x + offset, y)
                    for offset in range(length)
                )
                segments.append(segment)

    # 纵向线段
    for x in range(1, BOARD_SIZE + 1):
        for length in range(3, BOARD_SIZE + 1):
            for start_y in range(1, BOARD_SIZE - length + 2):
                segment = tuple(
                    (x, start_y + offset)
                    for offset in range(length)
                )
                segments.append(segment)

    return segments


ALL_CANNON_SEGMENTS = build_all_cannon_segments()
SEGMENT_TO_ID = {
    segment: i
    for i, segment in enumerate(ALL_CANNON_SEGMENTS)
}
SEGMENT_COUNT = len(ALL_CANNON_SEGMENTS)


PLACE_OFFSET = 0
UPGRADE_OFFSET = PLACE_OFFSET + BOARD_CELLS
EAT_OFFSET = UPGRADE_OFFSET + BOARD_CELLS
FIRE_OFFSET = EAT_OFFSET + BOARD_CELLS
MUZZLE_OFFSET = FIRE_OFFSET + SEGMENT_COUNT

ACTION_SPACE_SIZE = MUZZLE_OFFSET + SEGMENT_COUNT * 2


def cannon_positions_to_segment(
    cannon_data: dict[str, Any],
) -> tuple[tuple[int, int], ...]:
    positions = cannon_data["positions"]
    segment = tuple(
        (item["x"], item["y"])
        for item in positions
    )
    return segment


def segment_orientation(
    segment: tuple[tuple[int, int], ...],
) -> str:
    if len(segment) < 2:
        raise ValueError("炮管线段长度不足，无法判断方向。")

    x1, y1 = segment[0]
    x2, y2 = segment[1]

    if y1 == y2:
        return "H"
    if x1 == x2:
        return "V"

    raise ValueError(f"非法炮管线段，不是横向也不是纵向：{segment}")


def muzzle_direction_slot(
    segment: tuple[tuple[int, int], ...],
    direction: str,
) -> int:
    orientation = segment_orientation(segment)

    if orientation == "H":
        if direction == "left":
            return 0
        if direction == "right":
            return 1
        raise ValueError(f"横向炮管不能使用方向 {direction}")

    if orientation == "V":
        if direction == "up":
            return 0
        if direction == "down":
            return 1
        raise ValueError(f"纵向炮管不能使用方向 {direction}")

    raise ValueError(f"未知炮管方向：{orientation}")


def slot_to_muzzle_direction(
    segment: tuple[tuple[int, int], ...],
    slot: int,
) -> str:
    orientation = segment_orientation(segment)

    if slot not in (0, 1):
        raise ValueError(f"非法炮口槽位：{slot}")

    if orientation == "H":
        return "left" if slot == 0 else "right"

    if orientation == "V":
        return "up" if slot == 0 else "down"

    raise ValueError(f"未知炮管方向：{orientation}")


def encode_action(action: dict[str, Any]) -> int:
    action_type = action["type"]

    if action_type == "move":
        x = action["x"]
        y = action["y"]
        pos_idx = pos_to_index(x, y)

        if action["mode"] == "place":
            return PLACE_OFFSET + pos_idx

        if action["mode"] == "upgrade":
            return UPGRADE_OFFSET + pos_idx

        raise ValueError(f"未知 move mode：{action['mode']}")

    if action_type == "eat":
        x = action["x"]
        y = action["y"]
        pos_idx = pos_to_index(x, y)
        return EAT_OFFSET + pos_idx

    if action_type == "fire":
        cannon_data = action["cannon"]
        segment = cannon_positions_to_segment(cannon_data)
        segment_id = SEGMENT_TO_ID.get(segment)

        if segment_id is None:
            raise ValueError(f"未知炮管线段：{segment}")

        return FIRE_OFFSET + segment_id

    if action_type == "muzzle":
        cannon_data = action["cannon"]
        segment = cannon_positions_to_segment(cannon_data)
        segment_id = SEGMENT_TO_ID.get(segment)

        if segment_id is None:
            raise ValueError(f"未知炮管线段：{segment}")

        slot = muzzle_direction_slot(segment, action["direction"])
        return MUZZLE_OFFSET + segment_id * 2 + slot

    raise ValueError(f"未知动作类型：{action_type}")


def decode_action_id(action_id: int) -> dict[str, Any]:
    if not (0 <= action_id < ACTION_SPACE_SIZE):
        raise ValueError(f"action_id 超出范围：{action_id}")

    if PLACE_OFFSET <= action_id < UPGRADE_OFFSET:
        pos_idx = action_id - PLACE_OFFSET
        x, y = index_to_pos(pos_idx)
        return {
            "type": "move",
            "mode": "place",
            "x": x,
            "y": y,
        }

    if UPGRADE_OFFSET <= action_id < EAT_OFFSET:
        pos_idx = action_id - UPGRADE_OFFSET
        x, y = index_to_pos(pos_idx)
        return {
            "type": "move",
            "mode": "upgrade",
            "x": x,
            "y": y,
        }

    if EAT_OFFSET <= action_id < FIRE_OFFSET:
        pos_idx = action_id - EAT_OFFSET
        x, y = index_to_pos(pos_idx)
        return {
            "type": "eat",
            "x": x,
            "y": y,
        }

    if FIRE_OFFSET <= action_id < MUZZLE_OFFSET:
        segment_id = action_id - FIRE_OFFSET
        segment = ALL_CANNON_SEGMENTS[segment_id]
        return {
            "type": "fire",
            "segment": segment,
        }

    segment_slot = action_id - MUZZLE_OFFSET
    segment_id = segment_slot // 2
    slot = segment_slot % 2
    segment = ALL_CANNON_SEGMENTS[segment_id]
    direction = slot_to_muzzle_direction(segment, slot)

    return {
        "type": "muzzle",
        "segment": segment,
        "direction": direction,
    }


def action_matches_decoded(
    action: dict[str, Any],
    decoded: dict[str, Any],
) -> bool:
    action_type = action["type"]
    decoded_type = decoded["type"]

    if action_type != decoded_type:
        return False

    if action_type == "move":
        return (
            action["mode"] == decoded["mode"]
            and action["x"] == decoded["x"]
            and action["y"] == decoded["y"]
        )

    if action_type == "eat":
        return (
            action["x"] == decoded["x"]
            and action["y"] == decoded["y"]
        )

    if action_type in ("fire", "muzzle"):
        segment = cannon_positions_to_segment(action["cannon"])

        if segment != decoded["segment"]:
            return False

        if action_type == "muzzle":
            return action["direction"] == decoded["direction"]

        return True

    return False


def get_legal_action_id_map(game: Game) -> dict[int, dict[str, Any]]:
    legal_actions = game.get_legal_actions()
    result: dict[int, dict[str, Any]] = {}

    for action in legal_actions:
        action_id = encode_action(action)
        result[action_id] = action

    return result


def get_action_mask(game: Game) -> list[int]:
    mask = [0] * ACTION_SPACE_SIZE

    for action_id in get_legal_action_id_map(game):
        mask[action_id] = 1

    return mask


def id_to_legal_action(game: Game, action_id: int) -> dict[str, Any]:
    legal_map = get_legal_action_id_map(game)

    if action_id not in legal_map:
        decoded = decode_action_id(action_id)
        raise ValueError(
            f"当前 action_id 不合法：{action_id}，对应解码结果为 {decoded}"
        )

    return legal_map[action_id]