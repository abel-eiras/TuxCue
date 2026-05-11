from __future__ import annotations

from typing import Any

from PySide6.QtCore import QModelIndex, QObject, QPersistentModelIndex, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QSlider,
    QStyle,
    QStyleOptionButton,
    QStyleOptionSlider,
    QStyledItemDelegate,
    QWidget,
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
        label = "■" if is_playing else "▶"
        opt = QStyleOptionButton()
        opt.rect = option.rect
        opt.text = label
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

    def createEditor(
        self,
        parent: QWidget,
        option: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSlider:
        slider = QSlider(Qt.Horizontal, parent)
        slider.setRange(0, 100)
        slider.valueChanged.connect(lambda v: self._commit(slider))
        return slider

    def _commit(self, slider: QSlider) -> None:
        self.commitData.emit(slider)

    def setEditorData(
        self,
        editor: QWidget,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        volume: float = index.data(TrackRole.Volume) or 0.0
        slider: QSlider = editor  # type: ignore[assignment]
        slider.blockSignals(True)
        slider.setValue(int(volume * 100))
        slider.blockSignals(False)

    def setModelData(
        self,
        editor: QWidget,
        model: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        slider: QSlider = editor  # type: ignore[assignment]
        model.setData(index, slider.value() / 100.0, TrackRole.Volume)
