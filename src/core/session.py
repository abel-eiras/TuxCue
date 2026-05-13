from __future__ import annotations

import json
from pathlib import Path

from src.core.track import Track

_REQUIRED_FIELDS = {"id", "name", "path", "volume", "loop"}


def save(tracks: list[Track], path: Path) -> None:
    if not path.parent.exists():
        raise FileNotFoundError(f"Directory does not exist: {path.parent}")
    session_dir = path.parent
    entries = []
    for t in tracks:
        abs_path = t.path.resolve()
        try:
            rel_path: str | None = str(abs_path.relative_to(session_dir))
        except ValueError:
            rel_path = None
        entries.append({
            "id": t.id,
            "name": t.name,
            "path": str(abs_path),
            "path_relative": rel_path,
            "volume": t.volume,
            "loop": t.loop,
        })
    data = {"version": "1.0", "tracks": entries}
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
        abs_path = Path(item["path"])
        rel_str = item.get("path_relative")
        if not abs_path.exists() and rel_str is not None:
            candidate = path.parent / rel_str
            p = candidate if candidate.exists() else abs_path
        else:
            p = abs_path
        file_missing = not p.exists()
        tracks.append(
            Track(
                id=item["id"],
                name=item["name"],
                path=p,
                volume=item["volume"],
                loop=item["loop"],
                duration_s=0.0,
                missing_file=file_missing,
            )
        )
        if file_missing:
            errors.append(f"File not found: {p}")
    return tracks, errors
