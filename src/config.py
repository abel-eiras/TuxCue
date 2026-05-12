from __future__ import annotations

import json
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "tuxcue"
_CONFIG_FILE = _CONFIG_DIR / "config.json"
_DEFAULTS: dict[str, object] = {"language": "es"}


def load() -> dict[str, object]:
    if _CONFIG_FILE.exists():
        try:
            return {**_DEFAULTS, **json.loads(_CONFIG_FILE.read_text())}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save(data: dict[str, object]) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(data, indent=2))
