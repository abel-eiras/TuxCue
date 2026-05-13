"""
Tests for src/audio/engine.py and src/audio/stream.py.

Hardware-free: miniaudio.PlaybackDevice is mocked so no audio device is opened.
TrackStream.start() is also patched to avoid opening real devices.
"""

from __future__ import annotations

import array
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.audio.engine import AudioEngine
from src.audio.stream import TrackStream, _apply_volume

WAV_FIXTURE = Path(__file__).parent / "fixtures" / "test_tone.wav"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _noop_start(self: TrackStream) -> None:  # type: ignore[override]
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


# ---------------------------------------------------------------------------
# Unit: _apply_volume
# ---------------------------------------------------------------------------

class TestApplyVolume:
    def test_full_volume_returns_same_array(self) -> None:
        frames = array.array("h", [100, 200, -100])
        result = _apply_volume(frames, 1.0)
        assert result is frames

    def test_half_volume_halves_samples(self) -> None:
        frames = array.array("h", [1000, -1000, 0])
        result = _apply_volume(frames, 0.5)
        assert list(result) == [500, -500, 0]

    def test_zero_volume_silences_all(self) -> None:
        frames = array.array("h", [1000, -500])
        result = _apply_volume(frames, 0.0)
        assert list(result) == [0, 0]


# ---------------------------------------------------------------------------
# Unit: TrackStream state methods (no device opened)
# ---------------------------------------------------------------------------

class TestTrackStreamState:
    def _make_stream(self, volume: float = 0.8, loop: bool = False) -> TrackStream:
        return TrackStream(
            path=WAV_FIXTURE,
            volume=volume,
            loop=loop,
            on_end=lambda: None,
            on_error=lambda msg: None,
        )

    def test_set_volume_clamps_above_one(self) -> None:
        ts = self._make_stream()
        ts.set_volume(1.5)
        assert ts._volume == pytest.approx(1.0)

    def test_set_volume_clamps_below_zero(self) -> None:
        ts = self._make_stream()
        ts.set_volume(-0.1)
        assert ts._volume == pytest.approx(0.0)

    def test_set_volume_accepts_valid_value(self) -> None:
        ts = self._make_stream()
        ts.set_volume(0.5)
        assert ts._volume == pytest.approx(0.5)

    def test_set_loop_updates_flag(self) -> None:
        ts = self._make_stream(loop=False)
        ts.set_loop(True)
        assert ts._loop is True

    def test_stop_sets_stopped_flag(self) -> None:
        ts = self._make_stream()
        # Provide a fake closed device so stop() doesn't crash
        ts._device = MagicMock()
        ts.stop()
        assert ts._stopped is True
        ts._device.close.assert_called_once()


# ---------------------------------------------------------------------------
# Integration: AudioEngine behaviour (device mocked)
# ---------------------------------------------------------------------------

class TestAudioEnginePlay:
    def test_play_calls_on_start(self) -> None:
        engine = _make_engine()
        on_start, _, _ = _play_with_mock_start(engine)
        on_start.assert_called_once_with("t1")

    def test_play_registers_stream_so_is_playing_is_true(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine)
        assert engine.is_playing("t1") is True

    def test_play_is_noop_when_already_playing(self) -> None:
        engine = _make_engine()
        on_start1, _, _ = _play_with_mock_start(engine, track_id="t1")
        on_start2 = MagicMock()
        with patch.object(TrackStream, "start", _noop_start):
            engine.play("t1", WAV_FIXTURE, 0.8, False, on_start2, MagicMock(), MagicMock())
        on_start2.assert_not_called()


class TestAudioEngineStop:
    def test_stop_removes_stream(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine)
        with patch.object(TrackStream, "stop", lambda self: None):
            engine.stop("t1")
        assert engine.is_playing("t1") is False

    def test_stop_is_noop_when_not_playing(self) -> None:
        engine = _make_engine()
        # Should not raise
        engine.stop("nonexistent")

    def test_stop_calls_underlying_stream_stop(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine)
        stop_mock = MagicMock()
        with patch.object(TrackStream, "stop", stop_mock):
            engine.stop("t1")
        stop_mock.assert_called_once()


class TestAudioEngineStopAll:
    def test_stop_all_removes_all_streams(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine, track_id="t1")
        _play_with_mock_start(engine, track_id="t2")
        with patch.object(TrackStream, "stop", lambda self: None):
            engine.stop_all()
        assert engine.is_playing("t1") is False
        assert engine.is_playing("t2") is False

    def test_stop_all_is_noop_when_empty(self) -> None:
        engine = _make_engine()
        engine.stop_all()  # must not raise

    def test_stop_all_does_not_deadlock(self) -> None:
        import threading

        engine = _make_engine()
        _play_with_mock_start(engine, track_id="t1")
        _play_with_mock_start(engine, track_id="t2")

        with patch.object(TrackStream, "stop", lambda self: None):
            thread = threading.Thread(target=engine.stop_all)
            thread.start()
            thread.join(timeout=1.0)

        assert not thread.is_alive(), "stop_all() deadlocked — for loop must be outside the lock"


class TestAudioEngineSetVolume:
    def test_set_volume_delegates_to_stream(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine)
        vol_mock = MagicMock()
        with patch.object(TrackStream, "set_volume", vol_mock):
            engine.set_volume("t1", 0.5)
        vol_mock.assert_called_once_with(0.5)

    def test_set_volume_is_noop_when_not_playing(self) -> None:
        engine = _make_engine()
        # Should not raise
        engine.set_volume("nonexistent", 0.5)


class TestAudioEngineSetLoop:
    def test_set_loop_delegates_to_stream(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine)
        loop_mock = MagicMock()
        with patch.object(TrackStream, "set_loop", loop_mock):
            engine.set_loop("t1", True)
        loop_mock.assert_called_once_with(True)

    def test_set_loop_is_noop_when_not_playing(self) -> None:
        engine = _make_engine()
        # Should not raise
        engine.set_loop("nonexistent", True)


class TestAudioEngineIsPlaying:
    def test_is_playing_false_before_play(self) -> None:
        engine = _make_engine()
        assert engine.is_playing("t1") is False

    def test_is_playing_true_after_play(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine)
        assert engine.is_playing("t1") is True

    def test_is_playing_false_after_stop(self) -> None:
        engine = _make_engine()
        _play_with_mock_start(engine)
        with patch.object(TrackStream, "stop", lambda self: None):
            engine.stop("t1")
        assert engine.is_playing("t1") is False


class TestAudioEngineOnEndCallback:
    def test_on_end_called_when_stream_ends_naturally(self) -> None:
        """
        The internal _on_end closure should call on_end and remove the stream.
        We invoke it directly to simulate the audio thread reaching EOF.
        """
        engine = _make_engine()
        on_end = MagicMock()
        _play_with_mock_start(engine, on_end=on_end)

        # Retrieve the stream and call its _on_end (simulates audio thread EOF)
        stream = engine._streams["t1"]
        stream._on_end()

        on_end.assert_called_once_with("t1")
        assert engine.is_playing("t1") is False


class TestAudioEngineOnErrorCallback:
    def test_on_error_called_and_stream_removed(self) -> None:
        engine = _make_engine()
        on_error = MagicMock()
        _play_with_mock_start(engine, on_error=on_error)

        stream = engine._streams["t1"]
        stream._on_error("disk read failure")

        on_error.assert_called_once_with("t1", "disk read failure")
        assert engine.is_playing("t1") is False


class TestProtocolCompliance:
    def test_audio_engine_satisfies_iaudioengine_protocol(self) -> None:
        from src.core.interfaces import IAudioEngine

        engine = AudioEngine()
        assert isinstance(engine, IAudioEngine)
