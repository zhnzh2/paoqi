from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    action: dict[str, Any] = Field(..., description="结构化动作对象")
