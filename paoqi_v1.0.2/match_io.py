from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def save_match_result(
    result: dict,
    folder: str = "match_logs",
    prefix: str = "match",
) -> str:
    Path(folder).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{prefix}_{timestamp}.json"
    path = Path(folder) / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return str(path)