from __future__ import annotations

import base64
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.config import load as load_config
from src.config import save as save_config
from src.core.audio_controller import AudioController
from src.core.track import Track
from src.gui.filter_bar import FilterBar
from src.gui.proxy_model import TrackFilterProxyModel
from src.gui.track_table_model import Column, TrackRole, TrackTableModel
from src.gui.track_table_view import TrackTableView
from src.i18n import get_locale, set_locale, tr
from src.i18n.strings import SUPPORTED_LOCALES

_MAX_RECENT = 8

_DARK_CSS = """
QWidget { background-color: #2b2b2b; color: #e0e0e0; }
QMenuBar { background-color: #353535; color: #e0e0e0; }
QMenuBar::item:selected { background-color: #4a4a4a; }
QMenu { background-color: #353535; color: #e0e0e0; border: 1px solid #4a4a4a; }
QMenu::item:selected { background-color: #4a90d9; color: #ffffff; }
QToolBar { background-color: #353535; border-bottom: 1px solid #4a4a4a; spacing: 4px; }
QTableView { background-color: #2b2b2b; alternate-background-color: #323232; color: #e0e0e0; gridline-color: #3e3e3e; }
QTableView::item:selected { background-color: #4a90d9; color: #ffffff; }
QHeaderView::section { background-color: #353535; color: #e0e0e0; border: 1px solid #4a4a4a; padding: 2px; }
QLineEdit { background-color: #353535; color: #e0e0e0; border: 1px solid #4a4a4a; border-radius: 3px; padding: 2px 4px; }
QLineEdit:focus { border-color: #4a90d9; }
QScrollBar:vertical { background-color: #2b2b2b; width: 10px; border: none; }
QScrollBar::handle:vertical { background-color: #555; border-radius: 5px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background-color: #2b2b2b; height: 10px; border: none; }
QScrollBar::handle:horizontal { background-color: #555; border-radius: 5px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QRadioButton { color: #e0e0e0; spacing: 6px; }
QRadioButton::indicator { width: 14px; height: 14px; border-radius: 7px; border: 2px solid #777; background-color: #2b2b2b; }
QRadioButton::indicator:checked { background-color: #4a90d9; border-color: #4a90d9; }
QPushButton { background-color: #353535; color: #e0e0e0; border: 1px solid #4a4a4a; border-radius: 3px; padding: 3px 10px; }
QPushButton:hover { background-color: #4a4a4a; }
QPushButton:pressed { background-color: #4a90d9; color: #ffffff; }
QLabel { color: #e0e0e0; }
"""

class MainWindow(QMainWindow):
    def __init__(self, controller: AudioController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._session_path: Path | None = None

        _cfg = load_config()
        app_font = QApplication.instance().font()
        self._base_font_size: int = app_font.pointSize() if app_font.pointSize() > 0 else 9
        self._font_scale: int = int(_cfg.get("font_scale", 0))  # type: ignore[arg-type]
        self._theme: str = str(_cfg.get("theme", "light"))
        self._apply_stylesheet()

        self._model = TrackTableModel(self)
        self._proxy = TrackFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(Column.NAME)

        self._view = TrackTableView()
        self._view.setModel(self._proxy)
        self._restore_column_state()

        self._filter_bar = FilterBar()

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_shortcuts()
        self._connect_signals()
        self._pos_timer = QTimer(self)
        self._pos_timer.setInterval(100)
        self._pos_timer.timeout.connect(self._on_position_poll)
        self._pos_timer.start()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._filter_bar)
        layout.addWidget(self._view)
        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu(tr("menu_file"))
        menu.addAction(tr("menu_new"), self._on_new_session, "Ctrl+N")
        menu.addAction(tr("menu_open"), self._on_open, "Ctrl+O")
        menu.addAction(tr("menu_save"), self._on_save, "Ctrl+S")
        menu.addAction(tr("menu_save_as"), self._on_save_as, "Ctrl+Shift+S")
        menu.addSeparator()

        self._recent_menu: QMenu = menu.addMenu(tr("menu_recent"))
        self._rebuild_recent_menu()

        settings_menu = self.menuBar().addMenu(tr("menu_settings"))
        lang_menu = settings_menu.addMenu(tr("menu_language"))

        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        current = get_locale()
        for locale in SUPPORTED_LOCALES:
            action = lang_menu.addAction(tr(f"lang_{locale}"))
            action.setCheckable(True)
            action.setChecked(locale == current)
            action.setData(locale)
            lang_group.addAction(action)
        lang_group.triggered.connect(self._on_language_changed)

        theme_menu = settings_menu.addMenu(tr("menu_theme"))
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        for theme_id, label_key in (("light", "theme_light"), ("dark", "theme_dark")):
            action = theme_menu.addAction(tr(label_key))
            action.setCheckable(True)
            action.setChecked(theme_id == self._theme)
            action.setData(theme_id)
            theme_group.addAction(action)
        theme_group.triggered.connect(self._on_theme_changed)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        stop_all_action = toolbar.addAction(tr("toolbar_stop_all"))
        stop_all_action.triggered.connect(self._on_stop_all)

    def _build_shortcuts(self) -> None:
        for n in range(1, 10):
            sc = QShortcut(QKeySequence(f"Ctrl+{n}"), self)
            sc.activated.connect(lambda _n=n: self._on_track_hotkey(_n))
            sc_stop = QShortcut(QKeySequence(f"Ctrl+Shift+{n}"), self)
            sc_stop.activated.connect(lambda _n=n: self._on_track_stop_hotkey(_n))
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(lambda: self._zoom(+1))
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(lambda: self._zoom(+1))
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(lambda: self._zoom(-1))
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self._zoom_reset)

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
        self._controller.track_stopped.connect(
            lambda tid: self._model.set_pause_state(tid, False)
        )
        self._controller.playback_ended.connect(
            lambda tid: self._model.set_play_state(tid, False)
        )
        self._controller.playback_ended.connect(
            lambda tid: self._model.set_pause_state(tid, False)
        )
        self._controller.track_paused.connect(
            lambda tid: self._model.set_pause_state(tid, True)
        )
        self._controller.track_resumed.connect(
            lambda tid: self._model.set_pause_state(tid, False)
        )
        self._controller.track_stopped.connect(
            lambda tid: self._model.reset_cue_pos(tid)
        )
        self._controller.playback_ended.connect(
            lambda tid: self._model.reset_cue_pos(tid)
        )
        self._controller.track_error.connect(self._on_track_error)
        self._view.files_dropped.connect(self._on_files_dropped)
        self._view.seek_delegate.seek_requested.connect(self._on_seek)
        self._view.reset_delegate.reset_requested.connect(self._on_reset_track)
        self._view.remove_requested.connect(self._on_remove_tracks)

    # ── Recent files ──────────────────────────────────────────────────────────────────────────────────────────────────

    def _rebuild_recent_menu(self) -> None:
        self._recent_menu.clear()
        config = load_config()
        recent: list[str] = list(config.get("recent_files", []))  # type: ignore[arg-type]
        if not recent:
            empty_action = self._recent_menu.addAction(tr("menu_recent_empty"))
            empty_action.setEnabled(False)
            return
        for file_str in recent:
            path = Path(file_str)
            action = self._recent_menu.addAction(path.name)
            action.setToolTip(str(path))
            action.setData(str(path))
            action.triggered.connect(lambda checked=False, p=path: self._load_session(p))

    def _update_recent(self, path: Path) -> None:
        config = load_config()
        recent: list[str] = list(config.get("recent_files", []))  # type: ignore[arg-type]
        path_str = str(path)
        if path_str in recent:
            recent.remove(path_str)
        recent.insert(0, path_str)
        config["recent_files"] = recent[:_MAX_RECENT]
        save_config(config)
        self._rebuild_recent_menu()

    # ── Hotkeys ───────────────────────────────────────────────────────────────────────────

    def _on_track_hotkey(self, n: int) -> None:
        row = n - 1
        if row >= self._proxy.rowCount():
            return
        idx = self._proxy.index(row, 0)
        track_id: str = idx.data(TrackRole.TrackId)
        if track_id:
            self._on_play_stop(track_id)

    def _on_track_stop_hotkey(self, n: int) -> None:
        row = n - 1
        if row >= self._proxy.rowCount():
            return
        idx = self._proxy.index(row, 0)
        track_id: str = idx.data(TrackRole.TrackId)
        if track_id and self._controller.is_playing(track_id):
            self._controller.stop(track_id)

    # ── Signals ──────────────────────────────────────────────────────────────────────────

    def _on_language_changed(self, action: object) -> None:
        if not isinstance(action, QAction):
            return
        locale = action.data()
        config = load_config()
        config["language"] = locale
        save_config(config)
        set_locale(locale)
        QMessageBox.information(self, tr("dlg_lang_title"), tr("dlg_lang_body"))

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
            if self._controller.is_paused(track_id):
                self._controller.resume(track_id)
            else:
                self._controller.pause(track_id)
            return
        track = self._model.get_track(track_id)
        if track is not None:
            self._controller.play(track.id, track.path, track.volume, track.loop, track.cue_pos)

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
            self._model.set_pause_state(tid, False)
            self._model.reset_cue_pos(tid)

    def _on_seek(self, track_id: str, fraction: float) -> None:
        if self._controller.is_playing(track_id):
            self._controller.seek(track_id, fraction)
        else:
            self._model.set_cue_pos(track_id, fraction)

    def _on_position_poll(self) -> None:
        for track_id in self._model.all_track_ids():
            if self._controller.is_playing(track_id):
                pos = self._controller.get_position(track_id)
                self._model.set_seek_pos(track_id, pos)

    def _on_track_error(self, track_id: str, message: str) -> None:
        QMessageBox.warning(self, tr("dlg_error_title"), message)

    def _on_reset_track(self, track_id: str) -> None:
        if self._controller.is_playing(track_id):
            self._controller.stop(track_id)
        else:
            self._model.reset_cue_pos(track_id)

    def _on_remove_tracks(self, track_ids: list[str]) -> None:
        for tid in track_ids:
            if self._controller.is_playing(tid):
                self._controller.stop(tid)
            self._model.remove_track(tid)

    def _on_files_dropped(self, paths: list[Path]) -> None:
        from src.audio.probe import probe_duration
        for p in paths:
            track = Track.from_path(p)
            track.duration_s = probe_duration(p)
            self._model.add_track(track)

    def _on_new_session(self) -> None:
        if self._model.rowCount() > 0:
            reply = QMessageBox.question(
                self,
                tr("dlg_new_title"),
                tr("dlg_new_body"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._controller.stop_all()
        for tid in list(self._model.all_track_ids()):
            self._model.remove_track(tid)
        self._session_path = None

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dlg_open_title"), "", tr("dlg_open_filter")
        )
        if not path:
            return
        self._load_session(Path(path))

    def _load_session(self, path: Path) -> None:
        from src.audio.probe import probe_duration
        from src.core import session as session_manager
        tracks, errors = session_manager.load(path)
        self._controller.stop_all()
        for tid in list(self._model.all_track_ids()):
            self._model.remove_track(tid)
        for track in tracks:
            if not track.missing_file:
                track.duration_s = probe_duration(track.path)
            self._model.add_track(track)
        self._session_path = path
        self._update_recent(path)
        if errors:
            QMessageBox.warning(self, tr("dlg_missing_title"), "\n".join(errors))

    def _on_save(self) -> None:
        if self._session_path is None:
            self._on_save_as()
        else:
            self._save_to(self._session_path)

    def _on_save_as(self) -> None:
        dialog = QFileDialog(self, tr("dlg_save_title"), "", tr("dlg_open_filter"))
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setDefaultSuffix("tuxcue.json")
        if not dialog.exec():
            return
        paths = dialog.selectedFiles()
        if not paths:
            return
        self._session_path = Path(paths[0])
        self._save_to(self._session_path)

    def _save_to(self, path: Path) -> None:
        from src.core import session as session_manager
        tracks = [self._model.get_track(tid) for tid in self._model.all_track_ids()]
        valid = [t for t in tracks if t is not None]
        session_manager.save(valid, path)
        self._update_recent(path)

    # ── Zoom ─────────────────────────────────────────────────────────────────────────────

    def _zoom(self, delta: int) -> None:
        self._font_scale = max(-3, min(10, self._font_scale + delta))
        self._apply_stylesheet()

    def _zoom_reset(self) -> None:
        self._font_scale = 0
        self._apply_stylesheet()

    def _on_theme_changed(self, action: object) -> None:
        if not isinstance(action, QAction):
            return
        self._theme = action.data()
        self._apply_stylesheet()

    def _apply_stylesheet(self) -> None:
        size = max(6, self._base_font_size + self._font_scale)
        font_css = f"* {{ font-size: {size}pt; }}"
        theme_css = _DARK_CSS if self._theme == "dark" else ""
        QApplication.instance().setStyleSheet(theme_css + font_css)
        row_h = max(16, 24 + self._font_scale * 2)
        if hasattr(self, "_view"):
            self._view.verticalHeader().setDefaultSectionSize(row_h)

    # ── Column state persistence ──────────────────────────────────────────────────────────────────

    # Increment when columns are added/removed so stale saved state is discarded
    _COLUMN_STATE_VERSION = 2

    def _restore_column_state(self) -> None:
        config = load_config()
        if config.get("column_state_version") != self._COLUMN_STATE_VERSION:
            return
        state_b64: str = config.get("column_state", "")  # type: ignore[assignment]
        if state_b64:
            self._view.horizontalHeader().restoreState(base64.b64decode(state_b64))

    def _save_column_state(self) -> None:
        config = load_config()
        state_bytes = bytes(self._view.horizontalHeader().saveState())
        config["column_state"] = base64.b64encode(state_bytes).decode()
        config["column_state_version"] = self._COLUMN_STATE_VERSION
        config["font_scale"] = self._font_scale
        config["theme"] = self._theme
        save_config(config)

    def closeEvent(self, event: object) -> None:
        self._save_column_state()
        super().closeEvent(event)  # type: ignore[misc]
