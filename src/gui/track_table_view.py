from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractItemModel, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QStyleOptionViewItem,
    QTableView,
    QWidget,
)

from src.gui.delegates import (
    LoopButtonDelegate,
    PlayButtonDelegate,
    ResetButtonDelegate,
    SeekSliderDelegate,
    VolumeSliderDelegate,
)
from src.gui.track_table_model import Column, TrackRole
from src.i18n import tr

_SLIDER_COLUMNS = (Column.VOLUME, Column.SEEK)


class TrackTableView(QTableView):
    files_dropped: Signal = Signal(list)
    remove_requested: Signal = Signal(list)  # list[str] of track_ids

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._play_delegate = PlayButtonDelegate(self)
        self._loop_delegate = LoopButtonDelegate(self)
        self._reset_delegate = ResetButtonDelegate(self)
        self._volume_delegate = VolumeSliderDelegate(self)
        self._seek_delegate = SeekSliderDelegate(self)
        self._setup_delegates()
        self._setup_drag_drop()
        self._setup_columns()

    def _setup_delegates(self) -> None:
        self.setItemDelegateForColumn(Column.PLAY, self._play_delegate)
        self.setItemDelegateForColumn(Column.LOOP, self._loop_delegate)
        self.setItemDelegateForColumn(Column.RESET, self._reset_delegate)
        self.setItemDelegateForColumn(Column.VOLUME, self._volume_delegate)
        self.setItemDelegateForColumn(Column.SEEK, self._seek_delegate)

    def _setup_drag_drop(self) -> None:
        # DropOnly so Qt never initiates a row-drag, which would swallow slider MouseMove events
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAcceptDrops(True)

    def _setup_columns(self) -> None:
        from PySide6.QtWidgets import QHeaderView
        header = self.horizontalHeader()
        header.setSectionResizeMode(Column.NAME, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(Column.DURATION, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(Column.PLAY, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(Column.LOOP, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(Column.VOLUME, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(Column.SEEK, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(Column.RESET, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(Column.NAME, 150)
        self.setColumnWidth(Column.DURATION, 80)
        self.setColumnWidth(Column.PLAY, 50)
        self.setColumnWidth(Column.LOOP, 50)
        self.setColumnWidth(Column.RESET, 40)
        self.setColumnWidth(Column.VOLUME, 100)
        header.setSectionsMovable(True)

        vheader = self.verticalHeader()
        vheader.setVisible(True)
        vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vheader.setDefaultSectionSize(24)
        vheader.setMinimumWidth(28)

    def setModel(self, model: QAbstractItemModel | None) -> None:
        super().setModel(model)
        if model is not None:
            header = self.horizontalHeader()
            # Seek right after Duration; Reset between Play and Loop
            header.moveSection(Column.SEEK, 2)
            header.moveSection(header.visualIndex(Column.RESET), 4)

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
    def reset_delegate(self) -> ResetButtonDelegate:
        return self._reset_delegate

    @property
    def seek_delegate(self) -> SeekSliderDelegate:
        return self._seek_delegate

    def _selected_track_ids(self) -> list[str]:
        ids = []
        for idx in self.selectionModel().selectedRows():
            tid: str = idx.data(TrackRole.TrackId)
            if tid:
                ids.append(tid)
        return ids

    def contextMenuEvent(self, event: object) -> None:
        ids = self._selected_track_ids()
        if not ids:
            return
        menu = QMenu(self)
        remove_action = menu.addAction(tr("ctx_remove_track"))
        if menu.exec(event.globalPos()) == remove_action:  # type: ignore[attr-defined]
            self.remove_requested.emit(ids)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            ids = self._selected_track_ids()
            if ids:
                self.remove_requested.emit(ids)
                return
        super().keyPressEvent(event)

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
