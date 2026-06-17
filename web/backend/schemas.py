from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

class ActionRequest(BaseModel):
    action: dict[str, Any] = Field(..., description="结构化动作对象")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")
    confirm_password: str = Field(..., min_length=1, max_length=128, description="确认密码")
    intro_letter: str = Field(..., min_length=1, max_length=500, description="介绍信")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class UpdateProfileRequest(BaseModel):
    intro_letter: str = Field(..., min_length=0, max_length=500, description="介绍信")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=1, max_length=128, description="新密码")


class UpdateSettingsRequest(BaseModel):
    settings: dict[str, Any] = Field(..., description="设置键值对")
