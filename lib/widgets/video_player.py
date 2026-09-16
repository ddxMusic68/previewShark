from pathlib import Path
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


def _format_time(ms: int) -> str:
    total_seconds = ms // 1000
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

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