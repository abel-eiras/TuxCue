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
        self._seek_frame: int | None = None
        self._frames_played: int = 0
        self._total_frames: int = 0
        self._device: miniaudio.PlaybackDevice | None = None
        self._generator: Generator[array.array, int, None] | None = None

    def _probe_total_frames(self) -> int:
        """Return total frames at _SAMPLE_RATE by trying all supported probers."""
        probers = [
            miniaudio.wav_get_file_info,
            miniaudio.mp3_get_file_info,
            miniaudio.flac_get_file_info,
            miniaudio.vorbis_get_file_info,
        ]
        for probe in probers:
            try:
                info = probe(str(self._path))
                if info.sample_rate > 0:
                    duration_s = info.num_frames / info.sample_rate
                    return int(duration_s * _SAMPLE_RATE)
            except Exception:
                continue
        return 0

    def _make_generator(self) -> Generator[array.array, int, None]:
        """
        Generator that feeds decoded frames to the PlaybackDevice.

        Supports pause (yields silence without advancing the decoder),
        seek (reopens the file at a new position), and looping.
        Runs in the audio thread — must not block the main thread.
        """
        seek_to = 0
        while True:
            try:
                stream = miniaudio.stream_file(
                    str(self._path),
                    output_format=_SAMPLE_FORMAT,
                    nchannels=_NCHANNELS,
                    sample_rate=_SAMPLE_RATE,
                    frames_to_read=_FRAMES_TO_READ,
                    seek_frame=seek_to,
                )
                with self._lock:
                    self._frames_played = seek_to
                    self._seek_frame = None
                frames = next(stream)
                eof = False
                while True:
                    with self._lock:
                        if self._stopped:
                            return
                        paused = self._paused
                        vol = self._volume
                        pending_seek = self._seek_frame

                    if pending_seek is not None:
                        seek_to = pending_seek
                        break  # reopen stream at new position

                    if paused:
                        # Yield silence without advancing decoder position
                        silence = array.array("h", [0] * len(frames))
                        yield silence
                        continue

                    out = _apply_volume(frames, vol)
                    required_frames: int = yield out
                    with self._lock:
                        self._frames_played += required_frames
                    try:
                        frames = stream.send(required_frames)
                    except StopIteration:
                        eof = True
                        break
            except Exception as exc:
                self._on_error(str(exc))
                return

            if eof:
                with self._lock:
                    should_loop = self._loop
                if not should_loop:
                    self._on_end()
                    return
                seek_to = 0  # loop: restart from beginning

    def start(self) -> None:
        """Open the playback device and start streaming. Called from the main thread."""
        self._total_frames = self._probe_total_frames()
        gen = self._make_generator()
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

    def seek(self, fraction: float) -> None:
        """Schedule a seek to a position in [0.0, 1.0]. Thread-safe."""
        with self._lock:
            frame = int(max(0.0, min(1.0, fraction)) * self._total_frames)
            self._seek_frame = frame

    def position_fraction(self) -> float:
        """Return current playback position as a fraction in [0.0, 1.0]. Thread-safe."""
        with self._lock:
            if self._total_frames == 0:
                return 0.0
            return min(1.0, self._frames_played / self._total_frames)

    def set_volume(self, volume: float) -> None:
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))

    def set_loop(self, loop: bool) -> None:
        with self._lock:
            self._loop = loop
