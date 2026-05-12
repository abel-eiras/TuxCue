"""
Tests for src/gui/proxy_model.py — TrackFilterProxyModel filter behavior.

All filters are cumulative: text AND duration must both pass.
QApplication is created once per session (offscreen platform set by conftest).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

try:
    from PySide6.QtCore import QRegularExpression
    from PySide6.QtWidgets import QApplication

    _qt_available = True
except ImportError:
    _qt_available = False

pytestmark = pytest.mark.skipif(
    not _qt_available, reason="PySide6 not installed — GUI tests skipped"
)


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    return app  # type: ignore[return-value]


def _make_track(name: str, duration_s: float = 30.0) -> Track:
    from src.core.track import Track

    return Track(
        id=f"id-{name}",
        name=name,
        path=Path(f"/tmp/{name}.wav"),
        duration_s=duration_s,
    )


@pytest.fixture
def source_model(qapp: QApplication) -> TrackTableModel:
    from src.gui.track_table_model import TrackTableModel

    return TrackTableModel()


@pytest.fixture
def proxy(source_model: TrackTableModel) -> TrackFilterProxyModel:
    from src.gui.proxy_model import TrackFilterProxyModel

    p = TrackFilterProxyModel()
    p.setSourceModel(source_model)
    return p


class TestTextFilter:
    def test_matching_track_is_visible(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        source_model.add_track(_make_track("RainLoop"))
        proxy.setFilterRegularExpression(
            QRegularExpression("rain", QRegularExpression.CaseInsensitiveOption)
        )
        assert proxy.rowCount() == 1

    def test_nonmatching_track_is_hidden(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        source_model.add_track(_make_track("Thunder"))
        proxy.setFilterRegularExpression(
            QRegularExpression("rain", QRegularExpression.CaseInsensitiveOption)
        )
        assert proxy.rowCount() == 0

    def test_empty_filter_shows_all(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        source_model.add_track(_make_track("A"))
        source_model.add_track(_make_track("B"))
        proxy.setFilterRegularExpression(QRegularExpression(""))
        assert proxy.rowCount() == 2

    def test_filter_is_case_insensitive(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        source_model.add_track(_make_track("THUNDER"))
        proxy.setFilterRegularExpression(
            QRegularExpression("thunder", QRegularExpression.CaseInsensitiveOption)
        )
        assert proxy.rowCount() == 1

    def test_partial_match_passes(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        source_model.add_track(_make_track("DrumLoop_01"))
        proxy.setFilterRegularExpression(
            QRegularExpression("drum", QRegularExpression.CaseInsensitiveOption)
        )
        assert proxy.rowCount() == 1

    def test_multiple_tracks_partial_filter(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        source_model.add_track(_make_track("DrumLoop"))
        source_model.add_track(_make_track("BassLine"))
        source_model.add_track(_make_track("DrumFill"))
        proxy.setFilterRegularExpression(
            QRegularExpression("drum", QRegularExpression.CaseInsensitiveOption)
        )
        assert proxy.rowCount() == 2


class TestDurationFilter:
    def test_all_segment_shows_everything(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Short", duration_s=5.0))
        source_model.add_track(_make_track("Long", duration_s=600.0))
        proxy.set_duration_segment(DurationSegment.ALL)
        assert proxy.rowCount() == 2

    def test_under_30s_shows_short_track(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Short15", duration_s=15.0))
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 1

    def test_under_30s_hides_60s_track(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Long60", duration_s=60.0))
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 0

    def test_under_30s_boundary_29s_visible(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Boundary29", duration_s=29.9))
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 1

    def test_under_30s_boundary_30s_hidden(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Boundary30", duration_s=30.0))
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 0

    def test_s30_to_2m_includes_30s(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Exactly30", duration_s=30.0))
        proxy.set_duration_segment(DurationSegment.S30_TO_2M)
        assert proxy.rowCount() == 1

    def test_s30_to_2m_excludes_120s(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Exactly120", duration_s=120.0))
        proxy.set_duration_segment(DurationSegment.S30_TO_2M)
        assert proxy.rowCount() == 0

    def test_m2_to_5m_range(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Mid200", duration_s=200.0))
        source_model.add_track(_make_track("Short15", duration_s=15.0))
        proxy.set_duration_segment(DurationSegment.M2_TO_5M)
        assert proxy.rowCount() == 1

    def test_over_5m_shows_long_tracks(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Epic600", duration_s=600.0))
        source_model.add_track(_make_track("Short10", duration_s=10.0))
        proxy.set_duration_segment(DurationSegment.OVER_5M)
        assert proxy.rowCount() == 1

    def test_switching_segments_updates_filter(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("Short10", duration_s=10.0))
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 1
        proxy.set_duration_segment(DurationSegment.OVER_5M)
        assert proxy.rowCount() == 0
        proxy.set_duration_segment(DurationSegment.ALL)
        assert proxy.rowCount() == 1


class TestCombinedFilters:
    def test_text_and_duration_both_must_pass(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        # Rain: 15s — passes text "rain" AND duration UNDER_30S
        source_model.add_track(_make_track("RainLoop", duration_s=15.0))
        # Thunder: 15s — fails text filter
        source_model.add_track(_make_track("Thunder", duration_s=15.0))
        # Rain: 90s — passes text but fails UNDER_30S
        source_model.add_track(_make_track("RainFall", duration_s=90.0))

        proxy.setFilterRegularExpression(
            QRegularExpression("rain", QRegularExpression.CaseInsensitiveOption)
        )
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 1

    def test_text_match_but_duration_mismatch_hidden(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("DrumLoop", duration_s=200.0))
        proxy.setFilterRegularExpression(
            QRegularExpression("drum", QRegularExpression.CaseInsensitiveOption)
        )
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 0

    def test_duration_match_but_text_mismatch_hidden(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("BassLine", duration_s=10.0))
        proxy.setFilterRegularExpression(
            QRegularExpression("drum", QRegularExpression.CaseInsensitiveOption)
        )
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        assert proxy.rowCount() == 0

    def test_both_filters_cleared_shows_all(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("A", duration_s=10.0))
        source_model.add_track(_make_track("B", duration_s=300.0))
        source_model.add_track(_make_track("C", duration_s=9999.0))
        proxy.setFilterRegularExpression(QRegularExpression(""))
        proxy.set_duration_segment(DurationSegment.ALL)
        assert proxy.rowCount() == 3

    def test_combined_filters_correct_subset(
        self, source_model: TrackTableModel, proxy: TrackFilterProxyModel
    ) -> None:
        from src.gui.proxy_model import DurationSegment

        source_model.add_track(_make_track("DrumShort", duration_s=10.0))
        source_model.add_track(_make_track("DrumLong", duration_s=400.0))
        source_model.add_track(_make_track("BassShort", duration_s=10.0))
        source_model.add_track(_make_track("BassLong", duration_s=400.0))

        proxy.setFilterRegularExpression(
            QRegularExpression("drum", QRegularExpression.CaseInsensitiveOption)
        )
        proxy.set_duration_segment(DurationSegment.UNDER_30S)
        # Only DrumShort passes both filters
        assert proxy.rowCount() == 1
