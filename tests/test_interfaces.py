"""Tests for src/core/interfaces.py — IAudioEngine Protocol conformance."""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

from src.core.interfaces import IAudioEngine


class MinimalEngine:
    """A minimal concrete implementation of IAudioEngine for structural checks."""

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
        pass

    def stop(self, track_id: str) -> None:
        pass

    def stop_all(self) -> None:
        pass

    def set_volume(self, track_id: str, volume: float) -> None:
        pass

    def set_loop(self, track_id: str, loop: bool) -> None:
        pass

    def pause(self, track_id: str) -> None:
        pass

    def resume(self, track_id: str) -> None:
        pass

    def is_paused(self, track_id: str) -> bool:
        return False

    def is_playing(self, track_id: str) -> bool:
        return False


class TestIAudioEngineProtocol:
    def test_minimal_engine_satisfies_protocol(self) -> None:
        engine = MinimalEngine()
        assert isinstance(engine, IAudioEngine)

    def test_mock_with_spec_satisfies_protocol(self) -> None:
        mock = MagicMock(spec=MinimalEngine)
        assert isinstance(mock, IAudioEngine)

    def test_incomplete_object_does_not_satisfy_protocol(self) -> None:
        class Incomplete:
            def play(self, *args: object, **kwargs: object) -> None:
                pass
            # missing stop, stop_all, set_volume, set_loop, is_playing

        assert not isinstance(Incomplete(), IAudioEngine)
