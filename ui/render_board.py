#ui/render_board.py
from __future__ import annotations

from typing import Any
import pygame
import pygame.gfxdraw

from ui.constants import *
from ui.scale import ui
from ui.render_common import draw_text

def aa_filled_circle(
    surface: pygame.Surface,
    x: int,
    y: int,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    pygame.gfxdraw.filled_circle(surface, x, y, radius, color)
    pygame.gfxdraw.aacircle(surface, x, y, radius, color)


def aa_circle_outline(
    surface: pygame.Surface,
    x: int,
    y: int,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    pygame.gfxdraw.aacircle(surface, x, y, radius, color)

def draw_piece_disc(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    light_color: tuple[int, int, int],
    dark_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
) -> None:
    cx, cy = center

    # 外层深色
    aa_filled_circle(surface, cx, cy, radius, dark_color)

    # 中层主色
    aa_filled_circle(surface, cx, cy, radius - 3, light_color)

    # 边框
    aa_circle_outline(surface, cx, cy, radius, border_color)

def draw_hint_ring(
    surface: pygame.Surface,
    x: int,
    y: int,
    border_color: tuple[int, int, int],
    fill_color: tuple[int, int, int, int] | None = None,
    radius_padding: int = 6,
    border_width: int = 3,
    extra_outline_color: tuple[int, int, int] | None = None,
) -> None:
    rect = cell_rect(x, y)
    cx, cy = rect.center

    cell = ui.u(BOARD_CELL)
    radius = cell // 2 - ui.u(radius_padding)

    if fill_color is not None:
        overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(
            overlay,
            cell // 2,
            cell // 2,
            radius,
            fill_color,
        )
        pygame.gfxdraw.aacircle(
            overlay,
            cell // 2,
            cell // 2,
            radius,
            fill_color,
        )
        surface.blit(overlay, rect.topleft)

    for i in range(border_width):
        aa_circle_outline(surface, cx, cy, radius - i, border_color)

    if extra_outline_color is not None:
        aa_circle_outline(surface, cx, cy, radius + ui.u(2), extra_outline_color)

def draw_hover_cell_shadow(
    surface: pygame.Surface,
    hovered_cell: tuple[int, int] | None,
) -> None:
    if hovered_cell is None:
        return

    x, y = hovered_cell
    rect = cell_rect(x, y)

    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill(CELL_HOVER_FILL)
    surface.blit(overlay, rect.topleft)

def draw_arrow_hint_triangle(
    surface: pygame.Surface,
    points: list[tuple[int, int]],
) -> None:
    if len(points) != 3:
        return

    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)

    overlay = pygame.Surface((max_x - min_x + 1, max_y - min_y + 1), pygame.SRCALPHA)
    shifted = [(x - min_x, y - min_y) for x, y in points]

    pygame.gfxdraw.filled_polygon(overlay, shifted, ARROW_HINT_COLOR)
    pygame.gfxdraw.aapolygon(overlay, shifted, ARROW_HINT_COLOR)
    surface.blit(overlay, (min_x, min_y))

def draw_muzzle_arrow_hints(
    surface: pygame.Surface,
    cannon_infos: list[dict[str, Any]],
) -> None:
    for info in cannon_infos:
        if info.get("type") != "muzzle":
            continue

        cannon = info.get("cannon", {})
        positions = cannon.get("positions", [])
        if not positions:
            continue

        xs = [pos.get("x") for pos in positions if isinstance(pos.get("x"), int)]
        ys = [pos.get("y") for pos in positions if isinstance(pos.get("y"), int)]
        if not xs or not ys:
            continue

        direction = info.get("direction")
        cell = ui.u(BOARD_CELL)

        if direction == "left":
            target_x = min(xs)
            target_y = ys[0]
            rect = cell_rect(target_x, target_y)
            cx = rect.left + cell // 6
            cy = rect.centery
            points = [
                (cx - cell // 10, cy),
                (cx + cell // 10, cy - cell // 6),
                (cx + cell // 10, cy + cell // 6),
            ]

        elif direction == "right":
            target_x = max(xs)
            target_y = ys[0]
            rect = cell_rect(target_x, target_y)
            cx = rect.right - cell // 6
            cy = rect.centery
            points = [
                (cx + cell // 10, cy),
                (cx - cell // 10, cy - cell // 6),
                (cx - cell // 10, cy + cell // 6),
            ]

        elif direction == "up":
            target_x = xs[0]
            target_y = min(ys)
            rect = cell_rect(target_x, target_y)
            cx = rect.centerx
            cy = rect.top + cell // 6
            points = [
                (cx, cy - cell // 10),
                (cx - cell // 6, cy + cell // 10),
                (cx + cell // 6, cy + cell // 10),
            ]

        elif direction == "down":
            target_x = xs[0]
            target_y = max(ys)
            rect = cell_rect(target_x, target_y)
            cx = rect.centerx
            cy = rect.bottom - cell // 6
            points = [
                (cx, cy + cell // 10),
                (cx - cell // 6, cy - cell // 10),
                (cx + cell // 6, cy - cell // 10),
            ]
        else:
            continue

        draw_arrow_hint_triangle(surface, points)

def cell_rect(x: int, y: int) -> pygame.Rect:
    cell = ui.u(BOARD_CELL)
    px = ui.x(BOARD_ORIGIN_X) + (x - 1) * cell
    py = ui.y(BOARD_ORIGIN_Y) + (y - 1) * cell
    return pygame.Rect(px, py, cell, cell)

def cell_center(x: int, y: int) -> tuple[int, int]:
    rect = cell_rect(x, y)
    return rect.centerx, rect.centery

def draw_board_stars(surface: pygame.Surface) -> None:
    # 9x9 棋盘可先画 5 个点：中心 + 四角近中心
    star_points = [(3, 3), (3, 7), (5, 5), (7, 3), (7, 7)]

    for x, y in star_points:
        cx, cy = cell_center(x, y)
        aa_filled_circle(surface, cx, cy, 3, BOARD_STAR_COLOR)

def draw_capturable_targets(
    surface: pygame.Surface,
    capturable_cells: list[tuple[int, int]],
    hovered_cells: list[tuple[int, int]],
) -> None:
    hovered_set = set(hovered_cells)

    for x, y in capturable_cells:
        draw_hint_ring(
            surface,
            x,
            y,
            border_color=CAPTURABLE_COLOR,
            fill_color=CAPTURABLE_FILL,
            radius_padding=7,
            border_width=3,
            extra_outline_color=HOVER_CANNON_COLOR if (x, y) in hovered_set else None,
        )

def draw_cannon_highlights(
    surface: pygame.Surface,
    cannon_infos: list[dict[str, Any]],
    color: tuple[int, int, int],
    hovered_signatures: set[tuple] | None = None,
) -> None:
    if hovered_signatures is None:
        hovered_signatures = set()

    fill_color = CANNON_FILL if color == CANNON_HIGHLIGHT_COLOR else HOVER_CANNON_FILL

    for info in cannon_infos:
        cannon = info.get("cannon", {})
        positions = cannon.get("positions", [])
        signature = tuple((pos.get("x"), pos.get("y")) for pos in positions)

        centers: list[tuple[int, int]] = []
        for pos in positions:
            x = pos.get("x")
            y = pos.get("y")
            if isinstance(x, int) and isinstance(y, int):
                centers.append(cell_center(x, y))

                draw_hint_ring(
                    surface,
                    x,
                    y,
                    border_color=color,
                    fill_color=fill_color,
                    radius_padding=5,
                    border_width=3,
                    extra_outline_color=(
                        HOVER_CANNON_COLOR if signature in hovered_signatures else None
                    ),
                )

        if len(centers) >= 2:
            pygame.draw.lines(surface, color, False, centers, 4)
            pygame.draw.aalines(surface, color, False, centers)

            if signature in hovered_signatures:
                pygame.draw.lines(surface, HOVER_CANNON_COLOR, False, centers, 6)
                pygame.draw.aalines(surface, HOVER_CANNON_COLOR, False, centers)

def draw_board(
    surface: pygame.Surface,
    board_data: list[list[dict[str, Any] | None]],
    preview_board_data: list[list[dict[str, Any] | None]] | None,
    legal_highlights: dict[tuple[int, int], str],
    capturable_cells: list[tuple[int, int]],
    hovered_eat_cells: list[tuple[int, int]],
    cannon_highlights: list[dict[str, Any]],
    hovered_cannon_highlights: list[dict[str, Any]],
    hovered_cell: tuple[int, int] | None,
    fonts: dict[str, pygame.font.Font],
    arrow_hint_enabled: bool,
) -> None:
    cell = ui.u(BOARD_CELL)
    board_size_px = BOARD_SIZE * cell
    origin_x = ui.x(BOARD_ORIGIN_X)
    origin_y = ui.y(BOARD_ORIGIN_Y)

    board_rect = pygame.Rect(
        ui.x(BOARD_ORIGIN_X),
        ui.y(BOARD_ORIGIN_Y),
        board_size_px,
        board_size_px,
    )

    pygame.draw.rect(surface, BOARD_BG, board_rect, border_radius=6)
    pygame.draw.rect(surface, BOARD_LINE_DARK, board_rect, 3, border_radius=6)
    draw_hover_cell_shadow(surface, hovered_cell)

    # 高亮合法格
    for (x, y), mode in legal_highlights.items():
        if mode == "place":
            draw_hint_ring(
                surface,
                x,
                y,
                border_color=LEGAL_PLACE_COLOR,
                fill_color=LEGAL_PLACE_FILL,
                radius_padding=7,
                border_width=3,
            )
        else:
            draw_hint_ring(
                surface,
                x,
                y,
                border_color=LEGAL_UPGRADE_COLOR,
                fill_color=LEGAL_UPGRADE_FILL,
                radius_padding=7,
                border_width=3,
            )

    # 网格线
    for i in range(BOARD_SIZE + 1):
        px = origin_x + i * cell
        py = origin_y + i * cell

        pygame.draw.line(
            surface,
            BOARD_LINE_LIGHT,
            (px, origin_y),
            (px, origin_y + board_size_px),
            1,
        )
        pygame.draw.aaline(
            surface,
            BOARD_LINE_LIGHT,
            (px, origin_y),
            (px, origin_y + board_size_px),
        )

        pygame.draw.line(
            surface,
            BOARD_LINE_LIGHT,
            (origin_x, py),
            (origin_x + board_size_px, py),
            1,
        )
        pygame.draw.aaline(
            surface,
            BOARD_LINE_LIGHT,
            (origin_x, py),
            (origin_x + board_size_px, py),
        )
    draw_board_stars(surface)

    hovered_signatures = {
        tuple((pos.get("x"), pos.get("y")) for pos in info.get("cannon", {}).get("positions", []))
        for info in hovered_cannon_highlights
    }

    draw_cannon_highlights(
        surface,
        cannon_highlights,
        CANNON_HIGHLIGHT_COLOR,
        hovered_signatures=hovered_signatures,
    )

    if arrow_hint_enabled:
        draw_muzzle_arrow_hints(surface, cannon_highlights)

    draw_capturable_targets(
        surface,
        capturable_cells,
        hovered_eat_cells,
    )

    # 坐标标记
    for i in range(BOARD_SIZE):
        label = str(i + 1)
        draw_text(
            surface,
            label,
            fonts["small"],
            TEXT_COLOR,
            origin_x + i * cell + cell // 2 - ui.x(8),
            origin_y - ui.y(36),
        )
        draw_text(
            surface,
            label,
            fonts["small"],
            TEXT_COLOR,
            origin_x - ui.x(36),
            origin_y + i * cell + cell // 2 - ui.y(12),
        )

    # 棋子
    for y in range(1, BOARD_SIZE + 1):
        for x in range(1, BOARD_SIZE + 1):
            piece = board_data[y - 1][x - 1]
            if piece is None:
                continue

            color = piece.get("color")
            level = piece.get("level", "?")

            cx, cy = cell_center(x, y)
            radius = cell // 2 - ui.u(8)

            if color == "R":
                draw_piece_disc(
                    surface,
                    (cx, cy),
                    radius,
                    RED_PIECE_LIGHT,
                    RED_PIECE_DARK,
                    BOARD_LINE_DARK,
                )
            else:
                draw_piece_disc(
                    surface,
                    (cx, cy),
                    radius,
                    BLUE_PIECE_LIGHT,
                    BLUE_PIECE_DARK,
                    BOARD_LINE_DARK,
                )
            txt = fonts["piece"].render(str(level), True, (248, 248, 248))
            txt_rect = txt.get_rect(center=(cx, cy))
            surface.blit(txt, txt_rect)

    if preview_board_data is not None and preview_board_data != board_data:
        preview_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)

        for y in range(1, BOARD_SIZE + 1):
            for x in range(1, BOARD_SIZE + 1):
                piece = preview_board_data[y - 1][x - 1]
                if piece is None:
                    continue

                color = piece.get("color")
                level = piece.get("level", "?")

                cx, cy = cell_center(x, y)
                radius = cell // 2 - ui.u(8)

                if color == "R":
                    draw_piece_disc(
                        preview_surface,
                        (cx, cy),
                        radius,
                        RED_PIECE_LIGHT,
                        RED_PIECE_DARK,
                        BOARD_LINE_DARK,
                    )
                else:
                    draw_piece_disc(
                        preview_surface,
                        (cx, cy),
                        radius,
                        BLUE_PIECE_LIGHT,
                        BLUE_PIECE_DARK,
                        BOARD_LINE_DARK,
                    )

                txt = fonts["piece"].render(str(level), True, (232, 232, 232))
                txt_rect = txt.get_rect(center=(cx, cy))
                preview_surface.blit(txt, txt_rect)

        preview_surface.set_alpha(82)
        surface.blit(preview_surface, (0, 0))