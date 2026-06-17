"""
用户数据存储层 —— 管理 data/ 目录、注册表和用户文件夹。

目录结构:
    data/
      _registry.json          # {"next_uid": 11, "users": {"<username>": <uid>, ...}}
      user/
        user_1/
          profile.json        # {"uid": 1, "username": "zhnzh", "role": "站主", ...}
          password.hash       # "<salt>:<sha256_hex>"
        user_2/
          profile.json        # {"uid": 2, "username": "Yan", "role": "管理员", ...}
          password.hash
        user_6/
          profile.json        # {"uid": 6, "username": "OutsideSkyline", "role": "管理员", ...}
          password.hash
        user_11/
          profile.json        # {"uid": 11, "username": "...", "role": "用户", ...}
          password.hash
        ...

角色:
    - "站主"    —— 站点所有者，最高权限
    - "管理员"  —— 管理员
    - "用户"    —— 普通注册用户（默认）
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
USER_DIR = DATA_DIR / "user"
REGISTRY_PATH = DATA_DIR / "_registry.json"

# 预置账号：用户名 -> (uid, role)
PRESEED_ACCOUNTS: dict[str, tuple[int, str]] = {
    "zhnzh": (1, "站主"),
    "Yan": (2, "管理员"),
    "OutsideSkyline": (6, "管理员"),
}
PRESEED_PASSWORD = "paoqi"


def _ensure_data_dir() -> None:
    """确保 data/ 和 data/user/ 目录存在。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_DIR.mkdir(parents=True, exist_ok=True)
    gitkeep = DATA_DIR / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def _load_registry() -> dict[str, Any]:
    """加载注册表，如果不存在则创建包含预置账号的初始注册表。"""
    _ensure_data_dir()
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    # 创建初始注册表，包含预置账号
    users: dict[str, int] = {}
    for username, (uid, _role_val) in PRESEED_ACCOUNTS.items():
        users[username] = uid

    registry: dict[str, Any] = {"next_uid": 11, "users": users}
    _save_registry(registry)

    # 为预置账号创建用户文件夹
    _create_preseed_users()

    return registry


def _save_registry(registry: dict[str, Any]) -> None:
    """保存注册表到文件。"""
    _ensure_data_dir()
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _hash_password(password: str) -> str:
    """对密码进行加盐 SHA-256 哈希，返回 "salt:hash" 格式。"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    """验证密码是否与存储的哈希匹配。"""
    try:
        salt, h = stored.split(":", 1)
    except ValueError:
        return False
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == h


def _get_user_dir(uid: int) -> Path:
    """获取指定 UID 的用户文件夹路径。"""
    return USER_DIR / f"user_{uid}"


def _create_preseed_users() -> None:
    """为预置账号创建用户文件夹和 profile。仅在注册表不存在时调用。"""
    for username, (uid, role) in PRESEED_ACCOUNTS.items():
        user_dir = _get_user_dir(uid)
        if user_dir.exists():
            continue

        user_dir.mkdir(parents=True, exist_ok=True)

        profile: dict[str, Any] = {
            "uid": uid,
            "username": username,
            "role": role,
            "intro_letter": "",
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        (user_dir / "profile.json").write_text(
            json.dumps(profile, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (user_dir / "password.hash").write_text(
            _hash_password(PRESEED_PASSWORD),
            encoding="utf-8",
        )


def register_user(username: str, password: str, intro_letter: str) -> dict[str, Any]:
    """
    注册新用户。

    Args:
        username: 用户名（唯一）
        password: 密码（明文，将被哈希存储）
        intro_letter: 介绍信

    Returns:
        用户 profile 字典

    Raises:
        ValueError: 用户名已存在
    """
    registry = _load_registry()

    if username in registry["users"]:
        raise ValueError("用户名已存在")

    if username in PRESEED_ACCOUNTS:
        raise ValueError("用户名已存在")

    uid = registry["next_uid"]
    registry["next_uid"] = uid + 1
    registry["users"][username] = uid
    _save_registry(registry)

    # 创建用户文件夹
    user_dir = _get_user_dir(uid)
    user_dir.mkdir(parents=True, exist_ok=True)

    profile: dict[str, Any] = {
        "uid": uid,
        "username": username,
        "role": "用户",
        "intro_letter": intro_letter,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    (user_dir / "profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (user_dir / "password.hash").write_text(
        _hash_password(password),
        encoding="utf-8",
    )

    return profile


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """
    验证用户登录。

    Args:
        username: 用户名
        password: 密码（明文）

    Returns:
        用户 profile 字典，验证失败返回 None
    """
    registry = _load_registry()
    uid = registry["users"].get(username)
    if uid is None:
        return None

    user_dir = _get_user_dir(uid)
    hash_path = user_dir / "password.hash"
    if not hash_path.exists():
        return None

    stored = hash_path.read_text(encoding="utf-8").strip()
    if not _verify_password(password, stored):
        return None

    profile_path = user_dir / "profile.json"
    if not profile_path.exists():
        return None

    return json.loads(profile_path.read_text(encoding="utf-8"))


def get_user_by_uid(uid: int) -> dict[str, Any] | None:
    """通过 UID 获取用户 profile。"""
    profile_path = _get_user_dir(uid) / "profile.json"
    if not profile_path.exists():
        return None
    return json.loads(profile_path.read_text(encoding="utf-8"))


def get_user_by_username(username: str) -> dict[str, Any] | None:
    """通过用户名获取用户 profile。"""
    registry = _load_registry()
    uid = registry["users"].get(username)
    if uid is None:
        return None
    return get_user_by_uid(uid)


# -------------------- 用户设置 --------------------

DEFAULT_SETTINGS: dict[str, Any] = {
    "showRecordPanel": True,
    "showCoordInsideCell": False,
    "showDropHighlight": True,
    "showEatHighlight": True,
    "showMuzzleHighlight": True,
    "showFireHighlight": True,
    "showArrowHints": True,
    "showHoverPreview": True,
    "showCannonHoverEnhance": True,
    "compactSidebar": False,
}


def get_user_settings(uid: int) -> dict[str, Any]:
    """获取用户设置，如果不存在则返回默认设置。"""
    settings_path = _get_user_dir(uid) / "settings.json"
    if not settings_path.exists():
        return dict(DEFAULT_SETTINGS)
    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    # 合并默认值以处理新增的设置项
    merged = dict(DEFAULT_SETTINGS)
    merged.update(saved)
    return merged


def save_user_settings(uid: int, settings: dict[str, Any]) -> None:
    """保存用户设置。"""
    user_dir = _get_user_dir(uid)
    user_dir.mkdir(parents=True, exist_ok=True)
    settings_path = user_dir / "settings.json"
    # 只保存已知的设置项
    filtered = {k: v for k, v in settings.items() if k in DEFAULT_SETTINGS}
    settings_path.write_text(
        json.dumps(filtered, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# -------------------- Profile 更新 --------------------


def update_user_profile(uid: int, intro_letter: str) -> dict[str, Any]:
    """更新用户的介绍信。"""
    user_dir = _get_user_dir(uid)
    profile_path = user_dir / "profile.json"
    if not profile_path.exists():
        raise ValueError("用户不存在")

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["intro_letter"] = intro_letter
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return profile


def change_user_password(uid: int, old_password: str, new_password: str) -> bool:
    """修改用户密码，返回是否成功。"""
    user_dir = _get_user_dir(uid)
    hash_path = user_dir / "password.hash"
    if not hash_path.exists():
        raise ValueError("用户不存在")

    stored = hash_path.read_text(encoding="utf-8").strip()
    if not _verify_password(old_password, stored):
        return False

    hash_path.write_text(_hash_password(new_password), encoding="utf-8")
    return True
