#policy_model
from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn

from rl.action_codec import ACTION_SPACE_SIZE
from rl.dataset import FEATURE_DIM


class PolicyMLP(nn.Module):
    def __init__(
        self,
        input_dim: int = FEATURE_DIM,
        hidden_dim: int = 256,
        output_dim: int = ACTION_SPACE_SIZE,
    ) -> None:
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 1:
            x = x.unsqueeze(0)

        x = x.float()
        logits = self.net(x)
        return logits


class ActorCriticMLP(nn.Module):
    def __init__(
        self,
        input_dim: int = FEATURE_DIM,
        hidden_dim: int = 256,
        action_dim: int = ACTION_SPACE_SIZE,
    ) -> None:
        super().__init__()

        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        self.policy_head = nn.Linear(hidden_dim, action_dim)
        self.value_head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        if x.dim() == 1:
            x = x.unsqueeze(0)

        x = x.float()
        features = self.backbone(x)

        policy_logits = self.policy_head(features)
        state_value = self.value_head(features).squeeze(-1)

        return {
            "policy_logits": policy_logits,
            "state_value": state_value,
        }


def apply_action_mask_to_logits(
    logits: torch.Tensor,
    action_mask: torch.Tensor,
) -> torch.Tensor:
    if logits.dim() != 2:
        raise ValueError(f"logits 维度应为 2，实际为 {logits.shape}")

    if action_mask.dim() == 1:
        action_mask = action_mask.unsqueeze(0)

    if action_mask.shape != logits.shape:
        raise ValueError(
            f"action_mask 与 logits 形状不一致："
            f"logits={logits.shape}, mask={action_mask.shape}"
        )

    masked_logits = logits.clone()
    masked_logits[action_mask == 0] = -1e9
    return masked_logits


def select_action_id_from_model(
    model: nn.Module,
    features: list[int],
    action_mask: list[int],
    greedy: bool = False,
    device: str = "cpu",
) -> dict[str, Any]:
    if len(features) != FEATURE_DIM:
        raise ValueError(
            f"features 长度不正确：期望 {FEATURE_DIM}，实际 {len(features)}"
        )

    if len(action_mask) != ACTION_SPACE_SIZE:
        raise ValueError(
            f"action_mask 长度不正确：期望 {ACTION_SPACE_SIZE}，实际 {len(action_mask)}"
        )

    if sum(action_mask) == 0:
        raise ValueError("action_mask 中没有合法动作，无法选动作。")

    model.eval()

    with torch.no_grad():
        x = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
        mask_tensor = torch.tensor(action_mask, dtype=torch.float32, device=device).unsqueeze(0)

        logits = model(x)
        masked_logits = apply_action_mask_to_logits(logits, mask_tensor)

        if greedy:
            action_id = int(torch.argmax(masked_logits, dim=1).item())
        else:
            probs = torch.softmax(masked_logits, dim=1)
            action_id = int(torch.multinomial(probs[0], num_samples=1).item())

    return {
        "action_id": action_id,
        "logits": logits.cpu(),
        "masked_logits": masked_logits.cpu(),
    }


def select_action_id_from_actor_critic(
    model: ActorCriticMLP,
    features: list[int],
    action_mask: list[int],
    greedy: bool = False,
    device: str = "cpu",
) -> dict[str, Any]:
    if len(features) != FEATURE_DIM:
        raise ValueError(
            f"features 长度不正确：期望 {FEATURE_DIM}，实际 {len(features)}"
        )

    if len(action_mask) != ACTION_SPACE_SIZE:
        raise ValueError(
            f"action_mask 长度不正确：期望 {ACTION_SPACE_SIZE}，实际 {len(action_mask)}"
        )

    if sum(action_mask) == 0:
        raise ValueError("action_mask 中没有合法动作，无法选动作。")

    model.eval()

    with torch.no_grad():
        x = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
        mask_tensor = torch.tensor(action_mask, dtype=torch.float32, device=device).unsqueeze(0)

        output = model(x)
        policy_logits = output["policy_logits"]
        state_value = output["state_value"]

        masked_logits = apply_action_mask_to_logits(policy_logits, mask_tensor)

        if greedy:
            action_id = int(torch.argmax(masked_logits, dim=1).item())
        else:
            probs = torch.softmax(masked_logits, dim=1)
            action_id = int(torch.multinomial(probs[0], num_samples=1).item())

    return {
        "action_id": action_id,
        "policy_logits": policy_logits.cpu(),
        "masked_logits": masked_logits.cpu(),
        "state_value": state_value.cpu(),
    }