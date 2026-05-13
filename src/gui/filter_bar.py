from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.proxy_model import DurationSegment
from src.i18n import tr

_SEGMENT_KEYS: dict[DurationSegment, str] = {
    DurationSegment.ALL: "filter_all",
    DurationSegment.UNDER_30S: "filter_under_30s",
    DurationSegment.S30_TO_2M: "filter_30s_2m",
    DurationSegment.M2_TO_5M: "filter_2m_5m",
    DurationSegment.OVER_5M: "filter_over_5m",
}


class FilterBar(QWidget):
    text_changed: Signal = Signal(str)
    duration_segment_changed: Signal = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._search = QLineEdit()
        self._search.setPlaceholderText(tr("filter_search_placeholder"))
        self._search.textChanged.connect(self.text_changed)
        layout.addWidget(self._search)

        seg_row = QHBoxLayout()
        seg_row.addWidget(QLabel(tr("filter_duration_label")))
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        for seg in DurationSegment:
            btn = QRadioButton(tr(_SEGMENT_KEYS[seg]))
            self._button_group.addButton(btn, int(seg))
            seg_row.addWidget(btn)
            if seg == DurationSegment.ALL:
                btn.setChecked(True)

        self._button_group.idClicked.connect(self.duration_segment_changed)
        layout.addLayout(seg_row)
