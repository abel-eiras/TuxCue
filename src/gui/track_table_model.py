from __future__ import annotations

from enum import IntEnum
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QByteArray,
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtGui import QColor

from src.core.track import Track
from src.i18n import tr

_HEADER_KEYS = {
    0: "col_name",
    1: "col_duration",
    2: "col_play",
    3: "col_loop",
    4: "col_volume",
}


class Column(IntEnum):
    NAME = 0
    DURATION = 1
    PLAY = 2
    LOOP = 3
    VOLUME = 4


class TrackRole:
    PlayState = Qt.UserRole + 1   # bool — stream is active (playing or paused)
    LoopState = Qt.UserRole + 2   # bool
    Volume = Qt.UserRole + 3      # float
    TrackId = Qt.UserRole + 4     # str
    DurationS = Qt.UserRole + 5   # float
    MissingFile = Qt.UserRole + 6  # bool
    PauseState = Qt.UserRole + 7   # bool — paused (only meaningful when PlayState=True)


_MIME_TYPE = "application/x-tuxcue-row"


def _fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


class TrackTableModel(QAbstractTableModel):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)
        self._tracks: list[Track] = []
        self._play_states: dict[str, bool] = {}
        self._pause_states: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Required QAbstractTableModel overrides
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._tracks)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(Column)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            key = _HEADER_KEYS.get(section)
            return tr(key) if key else ""
        return None

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.DisplayRole,
    ) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._tracks)):
            return None
        track = self._tracks[index.row()]
        col = index.column()
        return self._resolve_data(track, col, role)

    def _resolve_data(self, track: Track, col: int, role: int) -> Any:
        if role == Qt.DisplayRole:
            return self._display_data(track, col)
        if role == Qt.EditRole and col == Column.NAME:
            return track.name
        if role == Qt.ForegroundRole and track.missing_file:
            return QColor("#cc4444")
        if role == Qt.ToolTipRole and track.missing_file:
            return tr("tooltip_missing", path=track.path)
        if role == TrackRole.PlayState:
            return self._play_states.get(track.id, False)
        if role == TrackRole.PauseState:
            return self._pause_states.get(track.id, False)
        if role == TrackRole.LoopState:
            return track.loop
        if role == TrackRole.Volume:
            return track.volume
        if role == TrackRole.TrackId:
            return track.id
        if role == TrackRole.DurationS:
            return track.duration_s
        if role == TrackRole.MissingFile:
            return track.missing_file
        return None

    def _display_data(self, track: Track, col: int) -> Any:
        if col == Column.NAME:
            return track.name
        if col == Column.DURATION:
            return _fmt_duration(track.duration_s)
        if col == Column.PLAY:
            if self._play_states.get(track.id, False) and not self._pause_states.get(track.id, False):
                return "⏸"
            return "▶"
        if col == Column.LOOP:
            return "↺" if track.loop else ""
        if col == Column.VOLUME:
            return f"{int(track.volume * 100)}%"
        return None

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.EditRole,
    ) -> bool:
        if not index.isValid():
            return False
        if role == Qt.EditRole and index.column() == Column.NAME:
            self._tracks[index.row()].name = str(value)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        if role == TrackRole.Volume and index.column() == Column.VOLUME:
            self._tracks[index.row()].volume = max(0.0, min(1.0, float(value)))
            self.dataChanged.emit(index, index, [Qt.DisplayRole, TrackRole.Volume])
            return True
        return False

    def get_track(self, track_id: str) -> Track | None:
        for t in self._tracks:
            if t.id == track_id:
                return t
        return None

    def all_track_ids(self) -> list[str]:
        return [t.id for t in self._tracks]

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlags:
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        if index.column() == Column.NAME:
            return base | Qt.ItemIsEditable
        return base

    # ------------------------------------------------------------------
    # Public mutation API
    # ------------------------------------------------------------------

    def add_track(self, track: Track) -> None:
        row = len(self._tracks)
        self.beginInsertRows(QModelIndex(), row, row)
        self._tracks.append(track)
        self.endInsertRows()

    def remove_track(self, track_id: str) -> None:
        for i, t in enumerate(self._tracks):
            if t.id == track_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._tracks.pop(i)
                self._play_states.pop(track_id, None)
                self._pause_states.pop(track_id, None)
                self.endRemoveRows()
                return

    def set_play_state(self, track_id: str, playing: bool) -> None:
        self._play_states[track_id] = playing
        self._notify_play_column(track_id)

    def set_pause_state(self, track_id: str, paused: bool) -> None:
        self._pause_states[track_id] = paused
        self._notify_play_column(track_id)

    def _notify_play_column(self, track_id: str) -> None:
        for row, track in enumerate(self._tracks):
            if track.id == track_id:
                idx = self.index(row, Column.PLAY)
                self.dataChanged.emit(idx, idx, [Qt.DisplayRole, TrackRole.PlayState, TrackRole.PauseState])
                return

    # ------------------------------------------------------------------
    # Drag & drop — internal row reorder only
    # ------------------------------------------------------------------

    def supportedDragActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def mimeTypes(self) -> list[str]:
        return [_MIME_TYPE]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        rows = sorted({i.row() for i in indexes if i.isValid()})
        data = QMimeData()
        data.setData(_MIME_TYPE, QByteArray(str(rows[0]).encode()))
        return data

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        if action != Qt.MoveAction or not data.hasFormat(_MIME_TYPE):
            return False
        src_row = int(bytes(data.data(_MIME_TYPE)).decode())
        dest_row = row if row >= 0 else len(self._tracks)
        if src_row == dest_row or src_row == dest_row - 1:
            return False
        if not self.beginMoveRows(QModelIndex(), src_row, src_row, QModelIndex(), dest_row):
            return False
        track = self._tracks.pop(src_row)
        insert_at = dest_row if dest_row < src_row else dest_row - 1
        self._tracks.insert(insert_at, track)
        self.endMoveRows()
        return True
