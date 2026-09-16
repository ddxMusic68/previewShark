from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


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

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget, 1)
        layout.addWidget(self.error_label)

        self.player.mediaStatusChanged.connect(self._on_media_status)

    def play_file(self, path: Path):
        self.error_label.hide()
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

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.error_label.setText(
                "Could not play this file. OBS MKV recordings may need "
                "remuxing or a codec supported by Windows."
            )
            self.error_label.show()
