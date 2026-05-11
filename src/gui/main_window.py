from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.audio_controller import AudioController
from src.core.track import Track
from src.gui.filter_bar import FilterBar
from src.gui.proxy_model import TrackFilterProxyModel
from src.gui.track_table_model import Column, TrackRole, TrackTableModel
from src.gui.track_table_view import TrackTableView


class MainWindow(QMainWindow):
    def __init__(self, controller: AudioController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._session_path: Path | None = None

        self._model = TrackTableModel(self)
        self._proxy = TrackFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(Column.NAME)

        self._view = TrackTableView()
        self._view.setModel(self._proxy)

        self._filter_bar = FilterBar()

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._connect_signals()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._filter_bar)
        layout.addWidget(self._view)
        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("&File")
        menu.addAction("&New Session", self._on_new_session, "Ctrl+N")
        menu.addAction("&Open…", self._on_open, "Ctrl+O")
        menu.addAction("&Save", self._on_save, "Ctrl+S")
        menu.addAction("Save &As…", self._on_save_as, "Ctrl+Shift+S")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        stop_all_action = toolbar.addAction("Stop All")
        stop_all_action.triggered.connect(self._on_stop_all)

    def _connect_signals(self) -> None:
        self._filter_bar.text_changed.connect(self._proxy.setFilterFixedString)
        self._filter_bar.duration_segment_changed.connect(
            lambda i: self._proxy.set_duration_segment(i)
        )
        self._view.play_delegate.play_stop_requested.connect(self._on_play_stop)
        self._view.loop_delegate.loop_toggled.connect(self._on_loop_toggle)
        self._model.dataChanged.connect(self._on_model_data_changed)
        self._controller.track_started.connect(
            lambda tid: self._model.set_play_state(tid, True)
        )
        self._controller.track_stopped.connect(
            lambda tid: self._model.set_play_state(tid, False)
        )
        self._controller.playback_ended.connect(
            lambda tid: self._model.set_play_state(tid, False)
        )
        self._controller.track_error.connect(self._on_track_error)
        self._view.files_dropped.connect(self._on_files_dropped)

    def _on_model_data_changed(
        self, top_left: QModelIndex, bottom_right: QModelIndex, roles: list[int]
    ) -> None:
        if TrackRole.Volume not in roles:
            return
        for row in range(top_left.row(), bottom_right.row() + 1):
            idx = self._model.index(row, Column.VOLUME)
            track_id: str = self._model.index(row, 0).data(TrackRole.TrackId)
            volume: float = self._model.data(idx, TrackRole.Volume) or 0.0
            if track_id:
                self._controller.set_volume(track_id, volume)

    def _on_play_stop(self, track_id: str) -> None:
        if self._controller.is_playing(track_id):
            self._controller.stop(track_id)
            return
        track = self._model.get_track(track_id)
        if track is not None:
            self._controller.play(track.id, track.path, track.volume, track.loop)

    def _on_loop_toggle(self, track_id: str) -> None:
        track = self._model.get_track(track_id)
        if track is None:
            return
        track.loop = not track.loop
        self._controller.set_loop(track_id, track.loop)

    def _on_stop_all(self) -> None:
        self._controller.stop_all()
        for tid in self._model.all_track_ids():
            self._model.set_play_state(tid, False)

    def _on_track_error(self, track_id: str, message: str) -> None:
        QMessageBox.warning(self, "Playback Error", message)

    def _on_files_dropped(self, paths: list[Path]) -> None:
        for p in paths:
            self._model.add_track(Track.from_path(p))

    def _on_new_session(self) -> None:
        if self._model.rowCount() > 0:
            reply = QMessageBox.question(
                self,
                "New Session",
                "Clear the current session?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        for tid in list(self._model.all_track_ids()):
            self._model.remove_track(tid)
        self._session_path = None

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Session", "", "TuxCue Sessions (*.json)"
        )
        if not path:
            return
        self._load_session(Path(path))

    def _load_session(self, path: Path) -> None:
        from src.core import session as session_manager
        tracks, errors = session_manager.load(path)
        for tid in list(self._model.all_track_ids()):
            self._model.remove_track(tid)
        for track in tracks:
            self._model.add_track(track)
        self._session_path = path
        if errors:
            QMessageBox.warning(self, "Missing Files", "\n".join(errors))

    def _on_save(self) -> None:
        if self._session_path is None:
            self._on_save_as()
        else:
            self._save_to(self._session_path)

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Session", "", "TuxCue Sessions (*.json)"
        )
        if not path:
            return
        self._session_path = Path(path)
        self._save_to(self._session_path)

    def _save_to(self, path: Path) -> None:
        from src.core import session as session_manager
        tracks = [self._model.get_track(tid) for tid in self._model.all_track_ids()]
        valid = [t for t in tracks if t is not None]
        session_manager.save(valid, path)
