#env.py
from __future__ import annotations

from typing import Any

from core.game import Game
from rl.action_codec import get_action_mask, id_to_legal_action
from rl.reward import get_step_reward
from rl.state_codec import encode_state


class PaoqiEnv:
    def __init__(self) -> None:
        self.game = Game()
        self.last_action_id: int | None = None

    def reset(self) -> tuple[dict[str, Any], dict[str, Any]]:
        self.game = Game()
        self.last_action_id = None

        obs = encode_state(self.game)
        info = self._build_info(
            acting_player=None,
            action_id=None,
            action=None,
        )
        return obs, info

    def _build_info(
        self,
        acting_player: str | None,
        action_id: int | None,
        action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        legal_actions = self.game.get_legal_actions()

        return {
            "current_player": self.game.current_player,
            "phase": self.game.phase,
            "winner": self.game.get_winner(),
            "is_terminal": self.game.is_terminal(),
            "legal_action_count": len(legal_actions),
            "action_mask": get_action_mask(self.game),
            "acting_player": acting_player,
            "last_action_id": action_id,
            "last_action": action,
        }

    def get_observation(self) -> dict[str, Any]:
        return encode_state(self.game)

    def get_action_mask(self) -> list[int]:
        return get_action_mask(self.game)

    def step(self, action_id: int) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        if self.game.is_terminal():
            raise ValueError("游戏已经结束，不能继续 step。")

        acting_player = self.game.current_player
        action = id_to_legal_action(self.game, action_id)

        self.game.apply_action(action)
        self.last_action_id = action_id

        obs = encode_state(self.game)
        reward = get_step_reward(self.game, acting_player)
        done = self.game.is_terminal()
        info = self._build_info(
            acting_player=acting_player,
            action_id=action_id,
            action=action,
        )

        return obs, reward, done, info

    def render(self) -> str:
        return self.game.board.render()