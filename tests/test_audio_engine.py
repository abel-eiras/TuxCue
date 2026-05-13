from __future__ import annotations

import array
import time
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.audio.engine import AudioEngine
from src.audio.stream import TrackStream, _apply_volume

WAV_FIXTURE = Path(__file__).parent / "fixtures" / "sine_440hz_1s.wav"


def _noop_start(self: TrackStream, start_fraction: float = 0.0) -> None:  # type: ignore[override]
    """Replaces TrackStream.start() so no PlaybackDevice is opened."""
    pass


def _make_engine() -> AudioEngine:
    return AudioEngine()


def _play_with_mock_start(
    engine: AudioEngine,
    track_id: str = "t1",
    path: Path = WAV_FIXTURE,
    volume: float = 0.8,
    loop: bool = False,
    on_start: Callable[[str], None] | None = None,
    on_end: Callable[[str], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    s = MagicMock()
    e = MagicMock()
    err = MagicMock()
    on_start = on_start or s
    on_end = on_end or e
    on_error = on_error or err
    with patch.object(TrackStream, "start", _noop_start):
        engine.play(track_id, path, volume, loop, on_start, on_end, on_error)
    return s, e, err
