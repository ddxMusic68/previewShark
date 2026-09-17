from pathlib import Path
from PySide6.QtCore import QUrl, Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink


def _format_time(ms: int) -> str:
    total_seconds = ms // 1000
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


class CroppedVideoWidget(QWidget):
    """Draws the video frame itself so a draggable 9:16 guide can be drawn on top."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._show_guide = False
        self._dx = 0
        self._dy = 0
        self._dragging = False
        self._grab_pick = None

    def set_frame(self, frame):
        self._image = frame.toImage()
        self.update()

    def set_guide_visible(self, visible: bool):
        self._show_guide = bool(visible)
        if not self._show_guide:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def is_guide_visible(self) -> bool:
        return self._show_guide

    def guide_offset(self) -> tuple[int, int]:
        return self._dx, self._dy

    def _guide_rect(self) -> QRect:
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return QRect()
        gw = min(w, int(h * 9 / 16))
        gh = int(gw * 16 / 9)
        return QRect((w - gw) // 2 + self._dx, (h - gh) // 2 + self._dy, gw, gh)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._image is not None and not self._image.isNull():
            scaled = self._image.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawImage(
                (self.width() - scaled.width()) // 2,
                (self.height() - scaled.height()) // 2,
                scaled,
            )
        if self._show_guide:
            rect = self._guide_rect()
            if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                painter.setPen(QPen(QColor(0, 255, 0, 200), 2))
                painter.drawRect(rect)
        painter.end()

    def _contains_guide(self, pos) -> bool:
        return self._show_guide and self._guide_rect().contains(pos)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if self._contains_guide(pos):
            self._dragging = True
            self._grab_pick = pos - self._guide_rect().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if self._dragging:
            rect = self._guide_rect()
            tl = pos - self._grab_pick
            max_x = self.width() - rect.width()
            max_y = self.height() - rect.height()
            tl.setX(max(0, min(tl.x(), max_x)))
            tl.setY(max(0, min(tl.y(), max_y)))
            self._dx = tl.x() - (self.width() - rect.width()) // 2
            self._dy = tl.y() - (self.height() - rect.height()) // 2
            self.update()
            event.accept()
        else:
            if self._contains_guide(pos):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.setCursor(
            Qt.CursorShape.OpenHandCursor
            if self._contains_guide(event.position().toPoint())
            else Qt.CursorShape.ArrowCursor
        )

    def leaveEvent(self, event):
        if not self._dragging:
            self.setCursor(Qt.CursorShape.ArrowCursor)


class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        self.video_widget = CroppedVideoWidget()
        self._sink = QVideoSink(self)
        self.player.setVideoOutput(self._sink)
        self._sink.videoFrameChanged.connect(self.video_widget.set_frame)

        self.guide_btn = QPushButton("9:16 Guide")
        self.guide_btn.setCheckable(True)
        self.guide_btn.toggled.connect(self.video_widget.set_guide_visible)

        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.time_label = QLabel("0:00 / 0:00")

        self._dragging = False

        controls = QHBoxLayout()
        controls.addWidget(self.slider, 1)
        controls.addWidget(self.time_label)
        controls.addWidget(self.guide_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget, 1)
        layout.addLayout(controls)
        layout.addWidget(self.error_label)

        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status)

    def play_file(self, path: Path):
        self.error_label.hide()
        self._dragging = False
        self.slider.setEnabled(True)
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()
        self.slider.setEnabled(False)
        self.time_label.setText("0:00 / 0:00")

    def unload(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.slider.setEnabled(False)
        self.time_label.setText("0:00 / 0:00")

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_slider_pressed(self):
        self._dragging = True

    def _on_slider_released(self):
        self._dragging = False
        self.player.setPosition(self.slider.value())

    def _on_position_changed(self, position):
        if not self._dragging:
            self.slider.setValue(position)
            duration = self.player.duration()
            self.time_label.setText(f"{_format_time(position)} / {_format_time(duration)}")

    def _on_duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.error_label.setText(
                "Could not play this file. OBS MKV recordings may need "
                "remuxing or a codec supported by Windows."
            )
            self.error_label.show()