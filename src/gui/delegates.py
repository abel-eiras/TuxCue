from __future__ import annotations

from typing import Any

from PySide6.QtCore import QModelIndex, QObject, QPersistentModelIndex, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionSlider,
    QWidget,
)

from src.gui.track_table_model import TrackRole


def _fmt_time(seconds: float) -> str:
    total_s = max(0, int(seconds))
    m, s = divmod(total_s, 60)
    return f"{m}:{s:02d}"


def _parse_time(text: str) -> float | None:
    """Parse 'M:SS' or plain seconds into a float. Returns None if invalid."""
    text = text.strip()
    try:
        if ":" in text:
            m_str, s_str = text.split(":", 1)
            return int(m_str) * 60 + float(s_str)
        return float(text)
    except (ValueError, IndexError):
        return None


class PlayButtonDelegate(QStyledItemDelegate):
    play_stop_requested: Signal = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def paint(
        self,
        painter: QPainter,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        is_playing: bool = index.data(TrackRole.PlayState) or False
        is_paused: bool = index.data(TrackRole.PauseState) or False
        opt = QStyleOptionButton()
        opt.rect = option.rect
        if is_playing and not is_paused:
            opt.text = "⏸"
        else:
            opt.text = "▶"
            if is_paused:
                # Render as a "checked" / sunken button to distinguish paused from stopped
                opt.state = opt.state | QStyle.State_On
        QApplication.style().drawControl(QStyle.CE_PushButton, opt, painter)

    def editorEvent(
        self,
        event: Any,
        model: Any,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        if event.type() == QMouseEvent.Type.MouseButtonRelease:
            track_id: str = index.data(TrackRole.TrackId)
            if track_id:
                self.play_stop_requested.emit(track_id)
            return True
        return False


class LoopButtonDelegate(QStyledItemDelegate):
    loop_toggled: Signal = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def paint(
        self,
        painter: QPainter,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        loop_on: bool = index.data(TrackRole.LoopState) or False
        label = "↺"
        opt = QStyleOptionButton()
        opt.rect = option.rect
        opt.text = label
        # Visually dim inactive loop button without a separate icon set
        if loop_on:
            opt.state |= QStyle.State_On
        QApplication.style().drawControl(QStyle.CE_PushButton, opt, painter)

    def editorEvent(
        self,
        event: Any,
        model: Any,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        if event.type() == QMouseEvent.Type.MouseButtonRelease:
            track_id: str = index.data(TrackRole.TrackId)
            if track_id:
                self.loop_toggled.emit(track_id)
            return True
        return False


class SeekSliderDelegate(QStyledItemDelegate):
    seek_requested: Signal = Signal(str, float)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def paint(
        self,
        painter: QPainter,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        pos: float = index.data(TrackRole.SeekPos) or 0.0
        duration_s: float = index.data(TrackRole.DurationS) or 0.0

        opt = QStyleOptionSlider()
        opt.rect = option.rect
        opt.minimum = 0
        opt.maximum = 1000
        opt.sliderValue = int(pos * 1000)
        opt.sliderPosition = opt.sliderValue
        opt.orientation = Qt.Horizontal
        opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderHandle
        opt.activeSubControls = QStyle.SC_None
        QApplication.style().drawComplexControl(QStyle.CC_Slider, opt, painter)

        if duration_s > 0:
            current_s = pos * duration_s
            text = f"{_fmt_time(current_s)} / {_fmt_time(duration_s)}"
            painter.save()
            painter.setPen(option.palette.text().color())
            painter.drawText(option.rect, Qt.AlignCenter | Qt.AlignVCenter, text)
            painter.restore()

    def createEditor(
        self,
        parent: QWidget,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignCenter)
        editor.setPlaceholderText("M:SS")
        return editor

    def setEditorData(
        self,
        editor: QWidget,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if not isinstance(editor, QLineEdit):
            return
        pos: float = index.data(TrackRole.SeekPos) or 0.0
        duration_s: float = index.data(TrackRole.DurationS) or 0.0
        editor.setText(_fmt_time(pos * duration_s))
        editor.selectAll()

    def setModelData(
        self,
        editor: QWidget,
        model: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if not isinstance(editor, QLineEdit):
            return
        duration_s: float = index.data(TrackRole.DurationS) or 0.0
        if duration_s <= 0:
            return
        seconds = _parse_time(editor.text())
        if seconds is None:
            return
        fraction = max(0.0, min(seconds / duration_s, 1.0))
        track_id: str = index.data(TrackRole.TrackId)
        if track_id:
            self.seek_requested.emit(track_id, fraction)

    def editorEvent(
        self,
        event: Any,
        model: Any,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        from PySide6.QtCore import QEvent
        if (
            event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove)
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            rect = option.rect
            x = max(0, min(int(event.position().x()) - rect.left(), rect.width()))
            fraction = x / rect.width() if rect.width() > 0 else 0.0
            track_id: str = index.data(TrackRole.TrackId)
            if track_id:
                self.seek_requested.emit(track_id, fraction)
            return True
        return False


class VolumeSliderDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def paint(
        self,
        painter: QPainter,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        volume: float = index.data(TrackRole.Volume) or 0.0
        opt = QStyleOptionSlider()
        opt.rect = option.rect
        opt.minimum = 0
        opt.maximum = 100
        opt.sliderValue = int(volume * 100)
        opt.sliderPosition = opt.sliderValue
        opt.orientation = Qt.Horizontal
        opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderHandle
        opt.activeSubControls = QStyle.SC_None
        QApplication.style().drawComplexControl(QStyle.CC_Slider, opt, painter)

    def editorEvent(
        self,
        event: Any,
        model: Any,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        from PySide6.QtCore import QEvent
        if (
            event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove)
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            rect = option.rect
            x = max(0, min(int(event.position().x()) - rect.left(), rect.width()))
            volume = x / rect.width() if rect.width() > 0 else 0.0
            model.setData(index, volume, TrackRole.Volume)
            return True
        return False
