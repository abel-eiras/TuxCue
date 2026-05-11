from __future__ import annotations

from enum import IntEnum

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel

from src.gui.track_table_model import TrackRole


class DurationSegment(IntEnum):
    ALL = 0
    UNDER_30S = 1
    S30_TO_2M = 2
    M2_TO_5M = 3
    OVER_5M = 4


_SEGMENT_BOUNDS: dict[DurationSegment, tuple[float, float]] = {
    DurationSegment.ALL: (0.0, float("inf")),
    DurationSegment.UNDER_30S: (0.0, 30.0),
    DurationSegment.S30_TO_2M: (30.0, 120.0),
    DurationSegment.M2_TO_5M: (120.0, 300.0),
    DurationSegment.OVER_5M: (300.0, float("inf")),
}


class TrackFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)
        self._segment = DurationSegment.ALL

    def set_duration_segment(self, seg: DurationSegment) -> None:
        self._segment = seg
        self.invalidateFilter()

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QModelIndex,
    ) -> bool:
        text_ok = super().filterAcceptsRow(source_row, source_parent)
        return text_ok and self._duration_filter_passes(source_row, source_parent)

    def _duration_filter_passes(
        self,
        source_row: int,
        source_parent: QModelIndex,
    ) -> bool:
        if self._segment == DurationSegment.ALL:
            return True
        idx = self.sourceModel().index(source_row, 0, source_parent)
        duration: float = self.sourceModel().data(idx, TrackRole.DurationS) or 0.0
        lo, hi = _SEGMENT_BOUNDS[self._segment]
        return lo <= duration < hi
