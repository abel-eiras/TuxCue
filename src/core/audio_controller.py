from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from .interfaces import IAudioEngine


class AudioController(QObject):
    """
    Sole mediator between the GUI layer and the audio backend.

    The GUI calls public methods (play, stop, …). The AudioEngine calls
    back via plain Python callables. This class converts those callbacks
    into Qt signals emitted on the main thread via Qt.QueuedConnection
    semantics — by having the callbacks invoke invokeMethod or by
    emitting signals directly when the callback already runs on the
    main thread (e.g. after a synchronous stop()).

    No method here may block. No method here imports from src/gui.
    """

    # Emitted when a stream successfully begins playback.
    track_started: Signal = Signal(str)  # track_id

    # Emitted when a stream is explicitly stopped by the user.
    track_stopped: Signal = Signal(str)  # track_id

    # Emitted when a non-looping stream reaches its natural end.
    playback_ended: Signal = Signal(str)  # track_id

    # Emitted when the audio backend reports an error for a track.
    track_error: Signal = Signal(str, str)  # track_id, human-readable message

    def __init__(self, engine: IAudioEngine, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._engine = engine

    # ------------------------------------------------------------------
    # Public API — called by the GUI layer
    # ------------------------------------------------------------------

    def play(self, track_id: str, path: Path, volume: float, loop: bool) -> None:
        """Request playback of track_id. Ignored if already playing."""
        self._engine.play(
            track_id=track_id,
            path=path,
            volume=volume,
            loop=loop,
            on_start=self._on_start,
            on_end=self._on_end,
            on_error=self._on_error,
        )

    def stop(self, track_id: str) -> None:
        """Stop track_id and reset its position. Ignored if not playing."""
        if not self._engine.is_playing(track_id):
            return
        self._engine.stop(track_id)
        self.track_stopped.emit(track_id)

    def stop_all(self) -> None:
        """Stop every active stream. Called by the global Stop All control."""
        self._engine.stop_all()

    def set_volume(self, track_id: str, volume: float) -> None:
        """Apply volume [0.0–1.0] to track_id in real time."""
        self._engine.set_volume(track_id, volume)

    def set_loop(self, track_id: str, loop: bool) -> None:
        """Toggle loop state on track_id while it may be playing."""
        self._engine.set_loop(track_id, loop)

    def is_playing(self, track_id: str) -> bool:
        return self._engine.is_playing(track_id)

    # ------------------------------------------------------------------
    # Private callbacks — called by AudioEngine from its own thread.
    # Qt signal emission is thread-safe; Qt queues the delivery to the
    # main thread automatically when connected with QueuedConnection.
    # ------------------------------------------------------------------

    def _on_start(self, track_id: str) -> None:
        self.track_started.emit(track_id)

    def _on_end(self, track_id: str) -> None:
        self.playback_ended.emit(track_id)

    def _on_error(self, track_id: str, message: str) -> None:
        self.track_error.emit(track_id, message)
