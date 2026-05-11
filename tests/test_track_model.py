"""
Tests for src/gui/track_table_model.py — TrackTableModel behavior.

QApplication is created once per session (offscreen platform set by conftest).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

try:
    from PySide6.QtCore import QMimeData, QModelIndex, Qt
    from PySide6.QtWidgets import QApplication

    _qt_available = True
except ImportError:
    _qt_available = False

pytestmark = pytest.mark.skipif(
    not _qt_available, reason="PySide6 not installed — GUI tests skipped"
)


@pytest.fixture(scope="session")
def qapp() -> "QApplication":
    app = QApplication.instance() or QApplication(sys.argv)
    return app  # type: ignore[return-value]


def _make_track(
    name: str = "Test",
    duration_s: float = 30.0,
    volume: float = 0.8,
    loop: bool = False,
) -> "Track":
    from src.core.track import Track

    return Track(
        id=f"id-{name}",
        name=name,
        path=Path(f"/tmp/{name}.wav"),
        volume=volume,
        loop=loop,
        duration_s=duration_s,
    )


@pytest.fixture
def model(qapp: "QApplication") -> "TrackTableModel":
    from src.gui.track_table_model import TrackTableModel

    return TrackTableModel()


class TestAddRemoveTrack:
    def test_add_track_increases_row_count(self, model: "TrackTableModel") -> None:
        assert model.rowCount() == 0
        model.add_track(_make_track("A"))
        assert model.rowCount() == 1
        model.add_track(_make_track("B"))
        assert model.rowCount() == 2

    def test_remove_track_decreases_row_count(self, model: "TrackTableModel") -> None:
        track = _make_track("X")
        model.add_track(track)
        assert model.rowCount() == 1
        model.remove_track(track.id)
        assert model.rowCount() == 0

    def test_remove_nonexistent_track_is_noop(self, model: "TrackTableModel") -> None:
        model.add_track(_make_track("A"))
        model.remove_track("no-such-id")
        assert model.rowCount() == 1

    def test_remove_clears_play_state(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import TrackRole

        track = _make_track("A")
        model.add_track(track)
        model.set_play_state(track.id, True)
        model.remove_track(track.id)
        # After re-adding a track with same id, play state should be absent
        model.add_track(track)
        idx = model.index(0, 0)
        assert model.data(idx, TrackRole.PlayState) is False


class TestDataRetrieval:
    def test_display_name(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("MySong"))
        idx = model.index(0, Column.NAME)
        assert model.data(idx, Qt.DisplayRole) == "MySong"

    def test_display_duration_formatted(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A", duration_s=125.0))
        idx = model.index(0, Column.DURATION)
        assert model.data(idx, Qt.DisplayRole) == "2:05"

    def test_display_duration_zero(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A", duration_s=0.0))
        idx = model.index(0, Column.DURATION)
        assert model.data(idx, Qt.DisplayRole) == "0:00"

    def test_track_id_role(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import TrackRole

        track = _make_track("A")
        model.add_track(track)
        idx = model.index(0, 0)
        assert model.data(idx, TrackRole.TrackId) == track.id

    def test_duration_s_role(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import TrackRole

        model.add_track(_make_track("A", duration_s=42.5))
        idx = model.index(0, 0)
        assert model.data(idx, TrackRole.DurationS) == pytest.approx(42.5)

    def test_loop_state_role(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import TrackRole

        model.add_track(_make_track("A", loop=True))
        idx = model.index(0, 0)
        assert model.data(idx, TrackRole.LoopState) is True

    def test_volume_role(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import TrackRole

        model.add_track(_make_track("A", volume=0.6))
        idx = model.index(0, 0)
        assert model.data(idx, TrackRole.Volume) == pytest.approx(0.6)

    def test_invalid_index_returns_none(self, model: "TrackTableModel") -> None:
        assert model.data(QModelIndex(), Qt.DisplayRole) is None

    def test_edit_role_name_column(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("EditMe"))
        idx = model.index(0, Column.NAME)
        assert model.data(idx, Qt.EditRole) == "EditMe"


class TestSetData:
    def test_setdata_name_updates_track(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("OldName"))
        idx = model.index(0, Column.NAME)
        result = model.setData(idx, "NewName", Qt.EditRole)
        assert result is True
        assert model.data(idx, Qt.DisplayRole) == "NewName"

    def test_setdata_wrong_column_returns_false(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        idx = model.index(0, Column.DURATION)
        assert model.setData(idx, "x", Qt.EditRole) is False

    def test_setdata_emits_data_changed(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        changed: list[tuple[int, int]] = []
        model.dataChanged.connect(
            lambda tl, br, _roles: changed.append((tl.row(), br.row()))
        )
        idx = model.index(0, Column.NAME)
        model.setData(idx, "B", Qt.EditRole)
        assert changed == [(0, 0)]


class TestPlayState:
    def test_default_play_state_is_false(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import TrackRole

        model.add_track(_make_track("A"))
        idx = model.index(0, 0)
        assert model.data(idx, TrackRole.PlayState) is False

    def test_set_play_state_to_true(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import TrackRole

        track = _make_track("A")
        model.add_track(track)
        model.set_play_state(track.id, True)
        idx = model.index(0, 0)
        assert model.data(idx, TrackRole.PlayState) is True

    def test_set_play_state_emits_data_changed(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column, TrackRole

        track = _make_track("A")
        model.add_track(track)
        changed_roles: list[list[int]] = []
        model.dataChanged.connect(lambda tl, br, roles: changed_roles.append(list(roles)))
        model.set_play_state(track.id, True)
        assert changed_roles, "dataChanged should have been emitted"
        assert TrackRole.PlayState in changed_roles[0]

    def test_set_play_state_unknown_id_is_noop(self, model: "TrackTableModel") -> None:
        model.add_track(_make_track("A"))
        # Should not raise; just silently store the state
        model.set_play_state("nonexistent", True)

    def test_display_play_column_reflects_state(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        track = _make_track("A")
        model.add_track(track)
        idx = model.index(0, Column.PLAY)
        assert model.data(idx, Qt.DisplayRole) == "▶"
        model.set_play_state(track.id, True)
        assert model.data(idx, Qt.DisplayRole) == "■"


class TestDragAndDrop:
    def test_move_row_down_reorders_list(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        a, b, c = _make_track("A"), _make_track("B"), _make_track("C")
        for t in (a, b, c):
            model.add_track(t)

        # Move row 0 (A) to after row 2 (C) → expect [B, C, A]
        indexes = [model.index(0, Column.NAME)]
        mime = model.mimeData(indexes)
        model.dropMimeData(mime, Qt.MoveAction, 3, 0, QModelIndex())

        names = [model.data(model.index(r, Column.NAME), Qt.DisplayRole) for r in range(3)]
        assert names == ["B", "C", "A"]

    def test_move_row_up_reorders_list(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        a, b, c = _make_track("A"), _make_track("B"), _make_track("C")
        for t in (a, b, c):
            model.add_track(t)

        # Move row 2 (C) to row 0 → expect [C, A, B]
        indexes = [model.index(2, Column.NAME)]
        mime = model.mimeData(indexes)
        model.dropMimeData(mime, Qt.MoveAction, 0, 0, QModelIndex())

        names = [model.data(model.index(r, Column.NAME), Qt.DisplayRole) for r in range(3)]
        assert names == ["C", "A", "B"]

    def test_drop_wrong_action_returns_false(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        indexes = [model.index(0, Column.NAME)]
        mime = model.mimeData(indexes)
        result = model.dropMimeData(mime, Qt.CopyAction, 0, 0, QModelIndex())
        assert result is False

    def test_drop_same_position_returns_false(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        model.add_track(_make_track("B"))
        indexes = [model.index(0, Column.NAME)]
        mime = model.mimeData(indexes)
        # Dropping row 0 at row 1 (== src+1) is a no-op
        result = model.dropMimeData(mime, Qt.MoveAction, 1, 0, QModelIndex())
        assert result is False

    def test_layout_changed_emitted_on_drop(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        model.add_track(_make_track("B"))
        layout_signals: list[int] = []
        model.layoutChanged.connect(lambda: layout_signals.append(1))

        indexes = [model.index(0, Column.NAME)]
        mime = model.mimeData(indexes)
        model.dropMimeData(mime, Qt.MoveAction, 2, 0, QModelIndex())
        assert layout_signals, "layoutChanged must fire after a successful drop"


class TestFlags:
    def test_name_column_is_editable(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        flags = model.flags(model.index(0, Column.NAME))
        assert flags & Qt.ItemIsEditable

    def test_other_columns_not_editable(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        for col in (Column.DURATION, Column.PLAY, Column.LOOP, Column.VOLUME):
            flags = model.flags(model.index(0, col))
            assert not (flags & Qt.ItemIsEditable)

    def test_all_rows_drag_enabled(self, model: "TrackTableModel") -> None:
        from src.gui.track_table_model import Column

        model.add_track(_make_track("A"))
        flags = model.flags(model.index(0, Column.NAME))
        assert flags & Qt.ItemIsDragEnabled

    def test_invalid_index_returns_drop_enabled_only(self, model: "TrackTableModel") -> None:
        flags = model.flags(QModelIndex())
        assert flags & Qt.ItemIsDropEnabled
