from __future__ import annotations

from PySide6.QtWidgets import QApplication

_DARK = """
/* ── Base ─────────────────────────────────────────────── */
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-size: 13px;
}

/* ── Main window / dialogs ────────────────────────────── */
QMainWindow, QDialog, QMessageBox {
    background-color: #1e1e1e;
}

/* ── Menu bar ─────────────────────────────────────────── */
QMenuBar {
    background-color: #252525;
    color: #e0e0e0;
    border-bottom: 1px solid #333;
    padding: 2px 0;
}
QMenuBar::item:selected, QMenuBar::item:pressed {
    background-color: #333;
    border-radius: 3px;
}
QMenu {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #383838;
    padding: 4px 0;
}
QMenu::item {
    padding: 5px 24px 5px 12px;
}
QMenu::item:selected {
    background-color: #2a4a7a;
}
QMenu::item:disabled {
    color: #666;
}
QMenu::separator {
    height: 1px;
    background-color: #333;
    margin: 4px 0;
}

/* ── Tool bar ─────────────────────────────────────────── */
QToolBar {
    background-color: #252525;
    border-bottom: 1px solid #333;
    spacing: 4px;
    padding: 2px 4px;
}
QToolBar::separator {
    width: 1px;
    background-color: #383838;
    margin: 4px 2px;
}
QToolButton {
    background-color: #2e2e2e;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px 10px;
}
QToolButton:hover {
    background-color: #383838;
    border-color: #666;
}
QToolButton:pressed {
    background-color: #1a1a1a;
}

/* ── Table ────────────────────────────────────────────── */
QTableView {
    background-color: #1e1e1e;
    alternate-background-color: #232323;
    color: #e0e0e0;
    gridline-color: #2e2e2e;
    selection-background-color: #2a4a7a;
    selection-color: #ffffff;
    border: 1px solid #333;
    border-radius: 4px;
}
QTableView::item {
    padding: 2px 4px;
}
QTableView::item:selected {
    background-color: #2a4a7a;
}
QHeaderView {
    background-color: #252525;
    border: none;
}
QHeaderView::section {
    background-color: #252525;
    color: #999;
    border: none;
    border-right: 1px solid #333;
    border-bottom: 1px solid #333;
    padding: 5px 6px;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}
QHeaderView::section:first {
    border-left: none;
}
QHeaderView::section:last {
    border-right: none;
}

/* ── Scroll bars ──────────────────────────────────────── */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 10px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #404040;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background-color: #555;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 10px;
    border: none;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #404040;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #555;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

/* ── Line edit ────────────────────────────────────────── */
QLineEdit {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px 7px;
    selection-background-color: #2a4a7a;
}
QLineEdit:focus {
    border-color: #4a90d9;
}
QLineEdit::placeholder {
    color: #666;
}

/* ── Buttons ──────────────────────────────────────────── */
QPushButton {
    background-color: #2e2e2e;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 5px 14px;
    min-width: 64px;
}
QPushButton:hover {
    background-color: #383838;
    border-color: #666;
}
QPushButton:pressed {
    background-color: #1a1a1a;
}
QPushButton:default {
    border-color: #4a90d9;
}

/* ── Radio buttons ────────────────────────────────────── */
QRadioButton {
    color: #e0e0e0;
    spacing: 5px;
}
QRadioButton::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #555;
    border-radius: 7px;
    background-color: #2a2a2a;
}
QRadioButton::indicator:checked {
    background-color: #4a90d9;
    border-color: #4a90d9;
}
QRadioButton::indicator:hover {
    border-color: #888;
}

/* ── Check boxes ──────────────────────────────────────── */
QCheckBox {
    color: #e0e0e0;
    spacing: 5px;
}
QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #555;
    border-radius: 3px;
    background-color: #2a2a2a;
}
QCheckBox::indicator:checked {
    background-color: #4a90d9;
    border-color: #4a90d9;
}

/* ── Labels ───────────────────────────────────────────── */
QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

/* ── Tooltips ─────────────────────────────────────────── */
QToolTip {
    background-color: #2e2e2e;
    color: #e0e0e0;
    border: 1px solid #555;
    padding: 4px 8px;
    border-radius: 3px;
}

/* ── Status bar ───────────────────────────────────────── */
QStatusBar {
    background-color: #252525;
    color: #888;
    border-top: 1px solid #333;
}

/* ── File dialogs ─────────────────────────────────────── */
QFileDialog {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
QFileDialog QListView, QFileDialog QTreeView {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #333;
}
"""


def apply_dark_theme(app: QApplication) -> None:
    app.setStyleSheet(_DARK)
