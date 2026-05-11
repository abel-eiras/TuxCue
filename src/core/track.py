from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Track:
    """Canonical data model for a single audio track. Framework-agnostic."""

    id: str
    name: str
    path: Path
    volume: float = 0.8
    loop: bool = False
    duration_s: float = 0.0

    def __post_init__(self) -> None:
        self.volume = max(0.0, min(1.0, self.volume))

    @classmethod
    def from_path(cls, path: Path) -> Track:
        return cls(
            id=str(uuid.uuid4()),
            name=path.stem,
            path=path.resolve(),
        )

    def with_volume(self, volume: float) -> Track:
        """Return a new Track with clamped volume; leaves original untouched."""
        return Track(
            id=self.id,
            name=self.name,
            path=self.path,
            volume=volume,
            loop=self.loop,
            duration_s=self.duration_s,
        )
