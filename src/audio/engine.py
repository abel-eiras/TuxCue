from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from src.audio.stream import TrackStream


class AudioEngine:
    """
    Pure-Python audio engine. Satisfies IAudioEngine structurally (Protocol).
    No PySide6 or Qt imports allowed in this module or its dependencies.
    """

    def __init__(self) -> None:
        self._streams: dict[str, TrackStream] = {}
        self._lock = threading.Lock()

    def play(
        self,
        track_id: str,
        path: Path,
        volume: float,
        loop: bool,
        on_start: Callable[[str], None],
        on_end: Callable[[str], None],
        on_error: Callable[[str, str], None],
    ) -> None:
        """Open and start a stream for track_id. No-op if already playing."""
        with self._lock:
            if track_id in self._streams:
                return

        def _on_end() -> None:
            self._remove(track_id)
            on_end(track_id)

        def _on_error(msg: str) -> None:
            self._remove(track_id)
            on_error(track_id, msg)

        stream = TrackStream(
            path=path,
            volume=volume,
            loop=loop,
            on_end=_on_end,
            on_error=_on_error,
        )
        with self._lock:
            self._streams[track_id] = stream

        try:
            stream.start()
        except Exception as exc:
            self._remove(track_id)
            on_error(track_id, str(exc))
            return

        on_start(track_id)

    def stop(self, track_id: str) -> None:
        """Stop and discard the stream for track_id. No-op if not playing."""
        stream = self._remove(track_id)
        if stream is not None:
            stream.stop()

    def stop_all(self) -> None:
        """Stop and discard every active stream."""
        with self._lock:
            ids = list(self._streams.keys())
        for track_id in ids:
            self.stop(track_id)

    def set_volume(self, track_id: str, volume: float) -> None:
        """Apply volume [0.0–1.0] to an active stream. No-op if not playing."""
        with self._lock:
            stream = self._streams.get(track_id)
        if stream is not None:
            stream.set_volume(volume)

    def set_loop(self, track_id: str, loop: bool) -> None:
        """Toggle loop state on an active stream. No-op if not playing."""
        with self._lock:
            stream = self._streams.get(track_id)
        if stream is not None:
            stream.set_loop(loop)

    def is_playing(self, track_id: str) -> bool:
        """Return True if a stream for track_id is currently active."""
        with self._lock:
            return track_id in self._streams

    def _remove(self, track_id: str) -> TrackStream | None:
        with self._lock:
            return self._streams.pop(track_id, None)
