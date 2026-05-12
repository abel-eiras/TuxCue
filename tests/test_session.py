"""Tests for src/core/session.py — save/load contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.session import load, save
from src.core.track import Track


def _make_track(
    tmp_path: Path, name: str = "sound", volume: float = 0.8, loop: bool = False
) -> Track:
    f = tmp_path / f"{name}.wav"
    f.touch()
    return Track(id=f"id-{name}", name=name, path=f.resolve(), volume=volume, loop=loop)


class TestSave:
    def test_creates_file_with_correct_structure(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path)
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        data = json.loads(out.read_text())
        assert data["version"] == "1.0"
        assert len(data["tracks"]) == 1
        assert data["tracks"][0]["id"] == track.id
        assert data["tracks"][0]["name"] == track.name

    def test_order_in_json_matches_list_order(self, tmp_path: Path) -> None:
        tracks = [_make_track(tmp_path, name=f"t{i}") for i in range(3)]
        out = tmp_path / "session.tuxcue.json"
        save(tracks, out)
        data = json.loads(out.read_text())
        ids = [entry["id"] for entry in data["tracks"]]
        assert ids == [t.id for t in tracks]

    def test_is_playing_never_serialized(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path)
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        data = json.loads(out.read_text())
        # Check the parsed structure: no track dict key may be "is_playing"
        for entry in data["tracks"]:
            assert "is_playing" not in entry

    def test_path_saved_as_absolute_string(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path)
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        data = json.loads(out.read_text())
        saved_path = data["tracks"][0]["path"]
        assert isinstance(saved_path, str)
        assert Path(saved_path).is_absolute()

    def test_volume_and_loop_saved_correctly(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path, volume=0.42, loop=True)
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        data = json.loads(out.read_text())
        assert data["tracks"][0]["volume"] == pytest.approx(0.42)
        assert data["tracks"][0]["loop"] is True

    def test_raises_if_parent_dir_missing(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path)
        out = tmp_path / "nonexistent_dir" / "session.tuxcue.json"
        with pytest.raises(FileNotFoundError):
            save([track], out)


class TestLoad:
    def test_loads_all_fields_correctly(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path, name="rain", volume=0.6, loop=True)
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        loaded, errors = load(out)
        assert errors == []
        assert len(loaded) == 1
        t = loaded[0]
        assert t.id == track.id
        assert t.name == track.name
        assert t.path == track.path
        assert t.volume == pytest.approx(0.6)
        assert t.loop is True

    def test_duration_s_always_zero_on_load(self, tmp_path: Path) -> None:
        track = Track(
            id="dur-id", name="d", path=(tmp_path / "d.wav"),
            volume=0.8, loop=False, duration_s=99.9
        )
        (tmp_path / "d.wav").touch()
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        loaded, _ = load(out)
        assert loaded[0].duration_s == pytest.approx(0.0)

    def test_missing_file_track_included_and_error_reported(self, tmp_path: Path) -> None:
        ghost = tmp_path / "ghost.wav"
        track = Track(id="g-id", name="ghost", path=ghost, volume=0.5, loop=False)
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        loaded, errors = load(out)
        assert len(loaded) == 1
        assert loaded[0].id == "g-id"
        assert loaded[0].missing_file is True
        assert len(errors) == 1
        assert "ghost.wav" in errors[0]

    def test_existing_file_track_missing_file_false(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path, name="present")
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        loaded, _ = load(out)
        assert loaded[0].missing_file is False

    def test_existing_file_track_has_no_error(self, tmp_path: Path) -> None:
        track = _make_track(tmp_path, name="present")
        out = tmp_path / "session.tuxcue.json"
        save([track], out)
        loaded, errors = load(out)
        assert errors == []
        assert len(loaded) == 1

    def test_invalid_json_missing_tracks_field_raises_value_error(self, tmp_path: Path) -> None:
        out = tmp_path / "bad.tuxcue.json"
        out.write_text(json.dumps({"version": "1.0"}))
        with pytest.raises(ValueError, match="tracks"):
            load(out)

    def test_invalid_json_missing_required_field_raises_value_error(self, tmp_path: Path) -> None:
        out = tmp_path / "bad.tuxcue.json"
        out.write_text(json.dumps({
            "version": "1.0",
            "tracks": [{"id": "x", "name": "x", "path": "/tmp/x.wav"}],  # missing volume, loop
        }))
        with pytest.raises(ValueError):
            load(out)

    def test_missing_file_raises_file_not_found_error(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load(tmp_path / "does_not_exist.tuxcue.json")

    def test_round_trip_save_load(self, tmp_path: Path) -> None:
        tracks = [
            _make_track(tmp_path, name="ambient", volume=0.7, loop=True),
            _make_track(tmp_path, name="thunder", volume=1.0, loop=False),
        ]
        out = tmp_path / "session.tuxcue.json"
        save(tracks, out)
        loaded, errors = load(out)
        assert errors == []
        assert len(loaded) == len(tracks)
        for original, restored in zip(tracks, loaded, strict=True):
            assert restored.id == original.id
            assert restored.name == original.name
            assert restored.path == original.path
            assert restored.volume == pytest.approx(original.volume)
            assert restored.loop == original.loop
