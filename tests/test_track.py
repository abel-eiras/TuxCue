"""Tests for src/core/track.py — Track dataclass invariants."""

from pathlib import Path

import pytest

from src.core.track import Track


class TestTrackFromPath:
    def test_name_is_stem(self, tmp_path: Path) -> None:
        f = tmp_path / "rain_loop.wav"
        f.touch()
        track = Track.from_path(f)
        assert track.name == "rain_loop"

    def test_path_is_absolute(self, tmp_path: Path) -> None:
        f = tmp_path / "sound.mp3"
        f.touch()
        track = Track.from_path(f)
        assert track.path.is_absolute()

    def test_id_is_unique(self, tmp_path: Path) -> None:
        f = tmp_path / "a.wav"
        f.touch()
        ids = {Track.from_path(f).id for _ in range(50)}
        assert len(ids) == 50

    def test_defaults(self, tmp_path: Path) -> None:
        f = tmp_path / "a.wav"
        f.touch()
        track = Track.from_path(f)
        assert track.volume == pytest.approx(0.8)
        assert track.loop is False
        assert track.duration_s == pytest.approx(0.0)


class TestVolumeClamp:
    def test_volume_above_one_clamped(self) -> None:
        track = Track(id="x", name="x", path=Path("/tmp/x.wav"), volume=1.5)
        assert track.volume == pytest.approx(1.0)

    def test_volume_below_zero_clamped(self) -> None:
        track = Track(id="x", name="x", path=Path("/tmp/x.wav"), volume=-0.1)
        assert track.volume == pytest.approx(0.0)

    def test_volume_at_boundary_zero(self) -> None:
        track = Track(id="x", name="x", path=Path("/tmp/x.wav"), volume=0.0)
        assert track.volume == pytest.approx(0.0)

    def test_volume_at_boundary_one(self) -> None:
        track = Track(id="x", name="x", path=Path("/tmp/x.wav"), volume=1.0)
        assert track.volume == pytest.approx(1.0)


class TestWithVolume:
    def test_returns_new_instance(self) -> None:
        track = Track(id="x", name="x", path=Path("/tmp/x.wav"), volume=0.5)
        new = track.with_volume(0.9)
        assert new is not track

    def test_original_unchanged(self) -> None:
        track = Track(id="x", name="x", path=Path("/tmp/x.wav"), volume=0.5)
        track.with_volume(0.9)
        assert track.volume == pytest.approx(0.5)

    def test_id_preserved(self) -> None:
        track = Track(id="my-id", name="x", path=Path("/tmp/x.wav"))
        new = track.with_volume(0.3)
        assert new.id == "my-id"

    def test_volume_clamped_in_copy(self) -> None:
        track = Track(id="x", name="x", path=Path("/tmp/x.wav"), volume=0.5)
        new = track.with_volume(2.0)
        assert new.volume == pytest.approx(1.0)
