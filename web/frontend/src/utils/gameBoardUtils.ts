import type { GameAction, GamePayload } from "../types/game";

export type HighlightType = "drop" | "eat" | "muzzle" | "fire" | null;

export function normalizeCannonPositions(cannon: any): Array<{ x: number; y: number }> {
  if (!cannon) {
    return [];
  }

  if (Array.isArray(cannon.cells)) {
    return cannon.cells
      .map((cell: any) => {
        if (cell && typeof cell.x === "number" && typeof cell.y === "number") {
          return { x: cell.x, y: cell.y };
        }

        if (Array.isArray(cell) && cell.length >= 2) {
          return { x: Number(cell[0]), y: Number(cell[1]) };
        }

        return null;
      })
      .filter((cell: any) => cell !== null);
  }

  if (Array.isArray(cannon.positions)) {
    return cannon.positions
      .map((pos: any) => {
        if (pos && typeof pos.x === "number" && typeof pos.y === "number") {
          return { x: pos.x, y: pos.y };
        }

        if (Array.isArray(pos) && pos.length >= 2) {
          return { x: Number(pos[0]), y: Number(pos[1]) };
        }

        return null;
      })
      .filter((pos: any) => pos !== null);
  }

  return [];
}

export function isInsideCannon(cannon: any, x: number, y: number): boolean {
  const positions = normalizeCannonPositions(cannon);
  return positions.some((pos) => pos.x === x && pos.y === y);
}

export function matchMuzzleActionByEndpoint(action: GameAction, x: number, y: number): boolean {
  if (action.type !== "muzzle") {
    return false;
  }

  const positions = normalizeCannonPositions(action.cannon);
  if (positions.length === 0) {
    return false;
  }

  const xs = positions.map((pos) => pos.x);
  const ys = positions.map((pos) => pos.y);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  if (action.direction === "left") {
    return x === minX && y >= minY && y <= maxY;
  }

  if (action.direction === "right") {
    return x === maxX && y >= minY && y <= maxY;
  }

  if (action.direction === "up") {
    return y === minY && x >= minX && x <= maxX;
  }

  if (action.direction === "down") {
    return y === maxY && x >= minX && x <= maxX;
  }

  return false;
}

export function getMuzzleEndpointDirection(action: GameAction): { x: number; y: number } | null {
  if (action.type !== "muzzle") {
    return null;
  }

  const positions = normalizeCannonPositions(action.cannon);
  if (positions.length === 0) {
    return null;
  }

  const xs = positions.map((pos) => pos.x);
  const ys = positions.map((pos) => pos.y);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  if (action.direction === "left") {
    return positions.find((p) => p.x === minX) ?? null;
  }

  if (action.direction === "right") {
    return positions.find((p) => p.x === maxX) ?? null;
  }

  if (action.direction === "up") {
    return positions.find((p) => p.y === minY) ?? null;
  }

  if (action.direction === "down") {
    return positions.find((p) => p.y === maxY) ?? null;
  }

  return null;
}

export function directionToArrow(direction: string | null | undefined): string | null {
  if (direction === "left") {
    return "←";
  }
  if (direction === "right") {
    return "→";
  }
  if (direction === "up") {
    return "↑";
  }
  if (direction === "down") {
    return "↓";
  }
  return null;
}

export function getArrowEndpointForDirection(
  cannon: any,
  direction: string | null | undefined
): { x: number; y: number } | null {
  const positions = normalizeCannonPositions(cannon);
  if (!direction || positions.length === 0) {
    return null;
  }

  const xs = positions.map((p) => p.x);
  const ys = positions.map((p) => p.y);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  if (direction === "left") {
    return positions.find((p) => p.x === minX) ?? null;
  }
  if (direction === "right") {
    return positions.find((p) => p.x === maxX) ?? null;
  }
  if (direction === "up") {
    return positions.find((p) => p.y === minY) ?? null;
  }
  if (direction === "down") {
    return positions.find((p) => p.y === maxY) ?? null;
  }

  return null;
}

export function buildArrowCells(payload: GamePayload | null): Record<string, string> {
  const result: Record<string, string> = {};

  if (!payload) {
    return result;
  }

  const actions = payload.legal_actions ?? [];

  if (payload.phase === "muzzle") {
    for (const action of actions) {
      if (action.type !== "muzzle") {
        continue;
      }

      const endpoint = getArrowEndpointForDirection(action.cannon, action.direction);
      const arrow = directionToArrow(action.direction);
      if (endpoint && arrow) {
        result[`${endpoint.x},${endpoint.y}`] = arrow;
      }
    }
  }

  if (payload.phase === "fire") {
    for (const action of actions) {
      if (action.type !== "fire") {
        continue;
      }

      const mouth = action.cannon?.mouth ?? action.cannon?.direction ?? null;
      const endpoint = getArrowEndpointForDirection(action.cannon, mouth);
      const arrow = directionToArrow(mouth);
      if (endpoint && arrow) {
        result[`${endpoint.x},${endpoint.y}`] = arrow;
      }
    }
  }

  return result;
}

export function findActionByCell(
  actions: GameAction[],
  phase: string,
  x: number,
  y: number
): GameAction | null {
  if (phase === "drop") {
    return (
      actions.find((action) => {
        return action.type === "move" && action.x === x && action.y === y;
      }) ?? null
    );
  }

  if (phase === "eat") {
    return (
      actions.find((action) => {
        return action.type === "eat" && action.x === x && action.y === y;
      }) ?? null
    );
  }

  if (phase === "muzzle") {
    const matched = actions.filter((action) => {
      return matchMuzzleActionByEndpoint(action, x, y);
    });

    if (matched.length === 1) {
      return matched[0];
    }

    return null;
  }

  if (phase === "fire") {
    const matched = actions.filter((action) => {
      return action.type === "fire" && isInsideCannon(action.cannon, x, y);
    });

    if (matched.length === 1) {
      return matched[0];
    }

    return null;
  }

  return null;
}

export function buildEmptyBoard(): ({ color: "R" | "B"; level: number } | null)[][] {
  return Array.from({ length: 9 }, () => Array.from({ length: 9 }, () => null));
}

export function buildHighlightedCells(
  payload: GamePayload | null,
  options: {
    showEatHighlight: boolean;
    showMuzzleHighlight: boolean;
    showFireHighlight: boolean;
  }
): Record<string, HighlightType> {
  const result: Record<string, HighlightType> = {};

  if (!payload) {
    return result;
  }

  const phase = payload.phase;
  const actions = payload.legal_actions ?? [];

  if (phase === "eat" && options.showEatHighlight) {
    for (const action of actions) {
      if (action.type === "eat" && typeof action.x === "number" && typeof action.y === "number") {
        result[`${action.x},${action.y}`] = "eat";
      }
    }
    return result;
  }

  if (phase === "muzzle" && options.showMuzzleHighlight) {
    for (const action of actions) {
      const endpoint = getMuzzleEndpointDirection(action);
      if (endpoint) {
        result[`${endpoint.x},${endpoint.y}`] = "muzzle";
      }
    }
    return result;
  }

  if (phase === "fire" && options.showFireHighlight) {
    for (const action of actions) {
      if (action.type !== "fire") {
        continue;
      }

      const positions = normalizeCannonPositions(action.cannon);
      for (const pos of positions) {
        result[`${pos.x},${pos.y}`] = "fire";
      }
    }
    return result;
  }

  return result;
}

export function buildHoveredDropHighlight(
  payload: GamePayload | null,
  hovered: { x: number; y: number } | null,
  showDropHighlight: boolean
): Record<string, HighlightType> {
  const result: Record<string, HighlightType> = {};

  if (!payload || !hovered) {
    return result;
  }

  if (payload.phase !== "drop" || !showDropHighlight) {
    return result;
  }

  const action = findActionByCell(payload.legal_actions, payload.phase, hovered.x, hovered.y);
  if (!action) {
    return result;
  }

  result[`${hovered.x},${hovered.y}`] = "drop";
  return result;
}

export function buildHoveredCannonCells(
  payload: GamePayload | null,
  hovered: { x: number; y: number } | null
): Record<string, true> {
  const result: Record<string, true> = {};

  if (!payload || !hovered) {
    return result;
  }

  const actions = payload.legal_actions ?? [];
  const phase = payload.phase;

  if (phase !== "muzzle" && phase !== "fire") {
    return result;
  }

  for (const action of actions) {
    if (phase === "muzzle" && action.type !== "muzzle") {
      continue;
    }
    if (phase === "fire" && action.type !== "fire") {
      continue;
    }

    const positions = normalizeCannonPositions(action.cannon);
    const containsHovered = positions.some(
      (pos) => pos.x === hovered.x && pos.y === hovered.y
    );

    if (!containsHovered) {
      continue;
    }

    for (const pos of positions) {
      result[`${pos.x},${pos.y}`] = true;
    }
  }

  return result;
}