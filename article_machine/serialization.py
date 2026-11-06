from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import yaml


def _normalize(value: Any) -> Any:
    return deepcopy(value)


def dump_structured_data(data: dict[str, Any]) -> str:
    payload = _normalize(data)
    return yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
    )


def _dump_json(data: dict[str, Any]) -> str:
    return json.dumps(_normalize(data), ensure_ascii=False, indent=2) + "\n"


def load_structured_text(text: str) -> dict[str, Any]:
    content = (text or "").strip()
    if not content:
        return {}
    loaded = yaml.safe_load(content)
    return loaded if isinstance(loaded, dict) else {}


def load_structured_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_structured_text(path.read_text(encoding="utf-8"))


def save_structured_file(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _dump_json(data) if path.suffix.lower() == ".json" else dump_structured_data(data)
    path.write_text(payload, encoding="utf-8")
    return path
