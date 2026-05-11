from __future__ import annotations

import json
from pathlib import Path

from src.core.track import Track

_REQUIRED_FIELDS = {"id", "name", "path", "volume", "loop"}


def save(tracks: list[Track], path: Path) -> None:
    if not path.parent.exists():
        raise FileNotFoundError(f"Directory does not exist: {path.parent}")
    data = {
        "version": "1.0",
        "tracks": [
            {
                "id": t.id,
                "name": t.name,
                "path": str(t.path.resolve()),
                "volume": t.volume,
                "loop": t.loop,
            }
            for t in tracks
        ],
    }
    path.write_text(json.dumps(data, indent=2))


def load(path: Path) -> tuple[list[Track], list[str]]:
    data = json.loads(path.read_text())
    if "tracks" not in data:
        raise ValueError("Invalid session file: missing 'tracks' field")
    tracks: list[Track] = []
    errors: list[str] = []
    for i, item in enumerate(data["tracks"]):
        missing = _REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(
                f"Track at index {i} is missing required fields: {missing}"
            )
        p = Path(item["path"])
        tracks.append(
            Track(
                id=item["id"],
                name=item["name"],
                path=p,
                volume=item["volume"],
                loop=item["loop"],
                duration_s=0.0,  # recalculated by AudioEngine when the file is opened
            )
        )
        if not p.exists():
            errors.append(f"File not found: {p}")
    return tracks, errors
