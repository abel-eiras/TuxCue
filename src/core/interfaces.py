from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class IAudioEngine(Protocol):
    """
    Contract that any audio backend must satisfy.

    Designed as a Protocol (structural subtyping) so the GUI test suite
    can use a mock without importing miniaudio at all. The real AudioEngine
    in src/audio/ implements this implicitly — no explicit inheritance needed.

    All methods are fire-and-forget from the caller's perspective.
    State changes are communicated back via the callbacks registered here,
    which AudioController wraps into Qt signals before forwarding to the GUI.
    """

    def play(
        self,
        track_id: str,
        path: Path,
        volume: float,
        loop: bool,
        on_start: Callable[[str], None],
        on_end: Callable[[str], None],
        on_error: Callable[[str, str], None],
        start_fraction: float = 0.0,
    ) -> None:
        """Open and start a stream for track_id. No-op if already playing."""
        ...

    def stop(self, track_id: str) -> None:
        """Stop and discard the stream for track_id. No-op if not playing."""
        ...

    def stop_all(self) -> None:
        """Stop and discard every active stream."""
        ...

    def set_volume(self, track_id: str, volume: float) -> None:
        """Apply volume [0.0–1.0] to an active stream immediately."""
        ...

    def set_loop(self, track_id: str, loop: bool) -> None:
        """Toggle loop state on an active stream."""
        ...

    def pause(self, track_id: str) -> None:
        """Pause the stream, keeping decoder position. No-op if not playing."""
        ...

    def resume(self, track_id: str) -> None:
        """Resume a paused stream from its saved position. No-op if not playing."""
        ...

    def is_paused(self, track_id: str) -> bool:
        """Return True if the stream exists and is currently paused."""
        ...

    def seek(self, track_id: str, fraction: float) -> None:
        """Seek to position fraction [0.0, 1.0]. No-op if not playing."""
        ...

    def get_position(self, track_id: str) -> float:
        """Return playback position as a fraction [0.0, 1.0]."""
        ...

    def is_playing(self, track_id: str) -> bool:
        """Return True if a stream for track_id is currently active."""
        ...
