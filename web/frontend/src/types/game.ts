export type PlayerColor = "R" | "B";

export type GameAction = Record<string, any>;

export type PieceData = {
  color: PlayerColor;
  level: number;
};

export type GameSnapshot = {
  board: (PieceData | null)[][];
  phase_info?: Record<string, any>;
  [key: string]: any;
};

export type GamePayload = {
  snapshot: GameSnapshot;
  legal_actions: GameAction[];
  legal_actions_snapshot: Record<string, any>;
  has_pending_auto_action: boolean;
  pending_auto_action: GameAction | null;
  auto_action_messages: string[];
  game_over: boolean;
  game_over_reason: string | null;
  winner: PlayerColor | null;
  history: string[];
  turn_number: number;
  current_player: PlayerColor;
  phase: string;
};

export type ApiSuccess<T = any> = {
  ok: true;
  message: string;
  data: T;
  result?: any;
  path?: string;
  history?: string[];
};

export type ApiFailure = {
  ok: false;
  message: string;
  data: null;
};

export type ApiResponse<T = any> = ApiSuccess<T> | ApiFailure;