from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QAbstractItemView, QTableView, QWidget

from src.gui.delegates import (
    LoopButtonDelegate,
    PlayButtonDelegate,
    SeekSliderDelegate,
    VolumeSliderDelegate,
)
from src.gui.track_table_model import Column


class TrackTableView(QTableView):
    files_dropped: Signal = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._play_delegate = PlayButtonDelegate(self)
        self._loop_delegate = LoopButtonDelegate(self)
        self._volume_delegate = VolumeSliderDelegate(self)
        self._seek_delegate = SeekSliderDelegate(self)
        self._setup_delegates()
        self._setup_drag_drop()
        self._setup_columns()

    def _setup_delegates(self) -> None:
        self.setItemDelegateForColumn(Column.PLAY, self._play_delegate)
        self.setItemDelegateForColumn(Column.LOOP, self._loop_delegate)
        self.setItemDelegateForColumn(Column.VOLUME, self._volume_delegate)
        self.setItemDelegateForColumn(Column.SEEK, self._seek_delegate)

    def _setup_drag_drop(self) -> None:
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAcceptDrops(True)

    def _setup_columns(self) -> None:
        header = self.horizontalHeader()
        from PySide6.QtWidgets import QHeaderView
        header.setSectionResizeMode(Column.NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(Column.DURATION, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(Column.PLAY, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(Column.LOOP, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(Column.VOLUME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(Column.SEEK, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(Column.DURATION, 80)
        self.setColumnWidth(Column.PLAY, 50)
        self.setColumnWidth(Column.LOOP, 50)

    @property
    def play_delegate(self) -> PlayButtonDelegate:
        return self._play_delegate

    @property
    def loop_delegate(self) -> LoopButtonDelegate:
        return self._loop_delegate

    @property
    def volume_delegate(self) -> VolumeSliderDelegate:
        return self._volume_delegate

    @property
    def seek_delegate(self) -> SeekSliderDelegate:
        return self._seek_delegate

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
