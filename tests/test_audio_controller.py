"""
Tests for src/core/audio_controller.py — AudioController signal/delegation behavior.

These tests use a mock AudioEngine (no Qt GUI, no miniaudio required).
pytest-qt is NOT needed here because we only test AudioController as a
QObject — we do need a QApplication for Qt to initialise signals.
"""

from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, call

import pytest

# QApplication must exist before any QObject is instantiated.
try:
    from PySide6.QtWidgets import QApplication

    _qt_available = True
except ImportError:
    _qt_available = False

pytestmark = pytest.mark.skipif(
    not _qt_available, reason="PySide6 not installed — GUI tests skipped"
)


@pytest.fixture(scope="session")
def qapp() -> "QApplication":
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    return app  # type: ignore[return-value]


@pytest.fixture
def mock_engine() -> MagicMock:
    """A MagicMock that structurally satisfies IAudioEngine."""
    engine = MagicMock()
    engine.is_playing.return_value = False
    return engine


@pytest.fixture
def controller(qapp: "QApplication", mock_engine: MagicMock) -> "AudioController":
    from src.core.audio_controller import AudioController

    return AudioController(engine=mock_engine)


class TestAudioControllerDelegation:
    def test_play_delegates_to_engine(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        controller.play("tid", Path("/tmp/a.wav"), 0.8, False)
        mock_engine.play.assert_called_once()
        kwargs = mock_engine.play.call_args.kwargs
        assert kwargs["track_id"] == "tid"
        assert kwargs["path"] == Path("/tmp/a.wav")
        assert kwargs["volume"] == pytest.approx(0.8)
        assert kwargs["loop"] is False

    def test_stop_delegates_to_engine(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        controller.stop("tid")
        mock_engine.stop.assert_called_once_with("tid")

    def test_stop_all_delegates_to_engine(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        controller.stop_all()
        mock_engine.stop_all.assert_called_once()

    def test_set_volume_delegates_to_engine(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        controller.set_volume("tid", 0.5)
        mock_engine.set_volume.assert_called_once_with("tid", 0.5)

    def test_set_loop_delegates_to_engine(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        controller.set_loop("tid", True)
        mock_engine.set_loop.assert_called_once_with("tid", True)

    def test_is_playing_delegates_to_engine(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        mock_engine.is_playing.return_value = True
        assert controller.is_playing("tid") is True


class TestAudioControllerSignals:
    def test_stop_emits_track_stopped(self, controller: "AudioController", mock_engine: MagicMock) -> None:
        received: list[str] = []
        controller.track_stopped.connect(received.append)
        controller.stop("tid")
        assert received == ["tid"]

    def test_on_start_callback_emits_track_started(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        received: list[str] = []
        controller.track_started.connect(received.append)
        # Simulate AudioEngine calling the on_start callback
        controller.play("tid", Path("/tmp/a.wav"), 0.8, False)
        on_start: Callable[[str], None] = mock_engine.play.call_args.kwargs["on_start"]
        on_start("tid")
        assert received == ["tid"]

    def test_on_end_callback_emits_playback_ended(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        received: list[str] = []
        controller.playback_ended.connect(received.append)
        controller.play("tid", Path("/tmp/a.wav"), 0.8, False)
        on_end: Callable[[str], None] = mock_engine.play.call_args.kwargs["on_end"]
        on_end("tid")
        assert received == ["tid"]

    def test_on_error_callback_emits_track_error(
        self, controller: "AudioController", mock_engine: MagicMock
    ) -> None:
        received: list[tuple[str, str]] = []
        controller.track_error.connect(lambda tid, msg: received.append((tid, msg)))
        controller.play("tid", Path("/tmp/a.wav"), 0.8, False)
        on_error: Callable[[str, str], None] = mock_engine.play.call_args.kwargs["on_error"]
        on_error("tid", "file not found")
        assert received == [("tid", "file not found")]
