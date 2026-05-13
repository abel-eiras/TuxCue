from __future__ import annotations

import array
import threading
from collections.abc import Callable, Generator
from pathlib import Path

import miniaudio

_SAMPLE_FORMAT = miniaudio.SampleFormat.SIGNED16
_NCHANNELS = 2
_SAMPLE_RATE = 44_100
_FRAMES_TO_READ = 1024
# s16 → 2 bytes per sample × nchannels gives the integer range for volume scaling
_S16_MAX = 32767


def _apply_volume(frames: array.array, volume: float) -> array.array:
    """Scale every sample in-place and return the same array."""
    if volume >= 1.0:
        return frames
    scaled = array.array(frames.typecode, (int(s * volume) for s in frames))
    return scaled


class TrackStream:
    """Manages a single miniaudio playback stream for one track."""

    def __init__(
        self,
        path: Path,
        volume: float,
        loop: bool,
        on_end: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        self._path = path
        self._volume = volume
        self._loop = loop
        self._on_end = on_end
        self._on_error = on_error
        self._lock = threading.Lock()
        self._stopped = False
        self._paused = False
        self._device: miniaudio.PlaybackDevice | None = None
        self._generator: Generator[array.array, int, None] | None = None

    def _make_generator(self) -> Generator[array.array, int, None]:
        """
        Generator that feeds decoded frames to the PlaybackDevice, applying
        volume and looping. Runs in the audio thread — must not block the main thread.

        When paused, yields silence while holding the current decoded frame so
        playback resumes from the exact same position without re-seeking.
        """
        while True:
            try:
                stream = miniaudio.stream_file(
                    str(self._path),
                    output_format=_SAMPLE_FORMAT,
                    nchannels=_NCHANNELS,
                    sample_rate=_SAMPLE_RATE,
                    frames_to_read=_FRAMES_TO_READ,
                )
                # Prime the generator before entering the send() loop
                frames = next(stream)
                while True:
                    with self._lock:
                        if self._stopped:
                            return
                        paused = self._paused
                        vol = self._volume

                    if paused:
                        # Yield silence; do NOT advance the file decoder so we
                        # resume from the exact position where we paused.
                        silence = array.array("h", [0] * len(frames))
                        yield silence
                        continue

                    out = _apply_volume(frames, vol)
                    required_frames: int = yield out
                    try:
                        frames = stream.send(required_frames)
                    except StopIteration:
                        break   # file exhausted — check loop flag
            except Exception as exc:
                self._on_error(str(exc))
                return

            with self._lock:
                should_loop = self._loop
            if not should_loop:
                self._on_end()
                return
            # Loop: fall through to while True and reopen the stream

    def start(self) -> None:
        """Open the playback device and start streaming. Called from the main thread."""
        gen = self._make_generator()
        # Prime so the device callback can use send() immediately
        next(gen)
        self._generator = gen
        self._device = miniaudio.PlaybackDevice(
            output_format=_SAMPLE_FORMAT,
            nchannels=_NCHANNELS,
            sample_rate=_SAMPLE_RATE,
        )
        self._device.start(gen)

    def stop(self) -> None:
        """Signal the stream to stop and close the device. Thread-safe."""
        with self._lock:
            self._stopped = True
        if self._device is not None:
            self._device.close()

    def pause(self) -> None:
        """Pause audio output; the file decoder position is preserved. Thread-safe."""
        with self._lock:
            self._paused = True

    def resume(self) -> None:
        """Resume from the paused position. Thread-safe."""
        with self._lock:
            self._paused = False

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    def set_volume(self, volume: float) -> None:
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))

    def set_loop(self, loop: bool) -> None:
        with self._lock:
            self._loop = loop
