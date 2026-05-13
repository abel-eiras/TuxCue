from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractItemModel, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QAbstractItemView, QStyleOptionViewItem, QTableView, QWidget

from src.gui.delegates import (
    LoopButtonDelegate,
    PlayButtonDelegate,
    SeekSliderDelegate,
    VolumeSliderDelegate,
)
from src.gui.track_table_model import Column

_SLIDER_COLUMNS = (Column.VOLUME, Column.SEEK)


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
        # DropOnly so Qt never initiates a row-drag, which would swallow slider MouseMove events
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
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
        header.setSectionsMovable(True)

    def setModel(self, model: QAbstractItemModel | None) -> None:
        super().setModel(model)
        if model is not None:
            # Place the seek (timeline) column right after Duration, before Play
            self.horizontalHeader().moveSection(Column.SEEK, 2)

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

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid() and index.column() in _SLIDER_COLUMNS:
                opt = QStyleOptionViewItem()
                opt.rect = self.visualRect(index)
                delegate = self.itemDelegate(index)
                if delegate and delegate.editorEvent(event, self.model(), opt, index):
                    return
        super().mouseMoveEvent(event)

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
