from __future__ import annotations

from typing import Any

from PySide6.QtCore import QModelIndex, QObject, QPersistentModelIndex, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionSlider,
)

from src.gui.track_table_model import TrackRole


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
