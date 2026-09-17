from pathlib import Path
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QCheckBox
)

from lib.services.file_service import scan_folder, detect_new_files, is_default_obs_name
from lib.services.file_operations import delete_file, rename_file, save_to_project
from lib.services.settings_service import (
    load_folder, save_folder, load_projects_folder, save_projects_folder,
    load_skip_rename_warning, save_skip_rename_warning
)
from lib.widgets.recording_list import RecordingList
from lib.widgets.video_player import VideoPlayer


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("preview_shark")
        self.resize(1100, 700)

        self.folder = load_folder()
        self.projects_folder = load_projects_folder()
        self.current = None
        self.last_snapshot: set[str] = set()

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._setup_timer()
        self.refresh()

    def _build_ui(self):
        self.folder_label = QLabel(str(self.folder))
        self.projects_label = QLabel(str(self.projects_folder))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Recording name")

        self.status = QLabel("Choose your OBS recordings folder.")
        self.status.setWordWrap(True)

        self.recording_list = RecordingList()
        self.player = VideoPlayer()

        choose = QPushButton("Choose OBS Folder")
        default = QPushButton("Default Folder")
        projects = QPushButton("Projects Folder")
        play = QPushButton("Play / Pause")
        delete = QPushButton("DELETE")
        rename = QPushButton("Rename")
        save = QPushButton("Save to Project")
        refresh = QPushButton("Refresh")

        self._btn_choose = choose
        self._btn_default = default
        self._btn_projects = projects
        self._btn_play = play
        self._btn_delete = delete
        self._btn_rename = rename
        self._btn_save = save
        self._btn_refresh = refresh

        top = QHBoxLayout()
        top.addWidget(choose)
        top.addWidget(default)
        top.addWidget(self.folder_label, 1)
        top.addWidget(refresh)

        project_row = QHBoxLayout()
        project_row.addWidget(projects)
        project_row.addWidget(self.projects_label, 1)

        controls = QHBoxLayout()
        controls.addWidget(play)
        controls.addWidget(delete)
        controls.addWidget(rename)
        controls.addWidget(save)

        left = QVBoxLayout()
        left.addWidget(QLabel("Recordings"))
        left.addWidget(self.recording_list)

        right = QVBoxLayout()
        right.addWidget(self.player, 1)
        right.addWidget(QLabel("Name:"))
        right.addWidget(self.name_edit)
        right.addLayout(controls)
        right.addWidget(self.status)

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.addLayout(left, 1)
        container_layout.addLayout(right, 3)

        main = QVBoxLayout(self)
        main.addLayout(top)
        main.addLayout(project_row)
        main.addWidget(container, 1)

    def _connect_signals(self):
        self._btn_choose.clicked.connect(self.choose_folder)
        self._btn_default.clicked.connect(self.set_default_folder)
        self._btn_projects.clicked.connect(self.choose_projects_folder)
        self._btn_play.clicked.connect(self.player.toggle_play)
        self._btn_delete.clicked.connect(self.delete_current)
        self._btn_rename.clicked.connect(self.rename_current)
        self._btn_save.clicked.connect(self.save)
        self._btn_refresh.clicked.connect(self.refresh)
        self.recording_list.itemClicked.connect(self._on_item_clicked)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key.Key_Space), self).activated.connect(self.player.toggle_play)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self).activated.connect(self.delete_current)
        QShortcut(QKeySequence(Qt.Key.Key_Up), self).activated.connect(self._nav_prev)
        QShortcut(QKeySequence(Qt.Key.Key_Down), self).activated.connect(self._nav_next)

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_for_new)
        self.timer.start(1500)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select OBS Recording Folder", str(self.folder)
        )
        if folder:
            self.folder = Path(folder)
            self.folder_label.setText(str(self.folder))
            self.refresh()

    def set_default_folder(self):
        if not self.folder or not self.folder.exists():
            QMessageBox.warning(self, "Default Folder", "Select an existing folder first.")
            return
        save_folder(self.folder)
        self.status.setText(f"Default folder saved to {save_folder.__globals__['SETTINGS_FILE']}")

    def choose_projects_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Projects Folder", str(self.projects_folder)
        )
        if folder:
            self.projects_folder = Path(folder)
            save_projects_folder(self.projects_folder)
            self.projects_label.setText(str(self.projects_folder))
            self.status.setText(f"Projects folder set: {self.projects_folder}")

    def save(self):
        if not self.current or not self.current.exists():
            return
        if not self._confirm_unrenamed():
            return
        dest = QFileDialog.getExistingDirectory(
            self,
            "Choose or create a folder in the projects directory",
            str(self.projects_folder),
        )
        if not dest:
            return
        try:
            self.player.unload()
            target = save_to_project(self.current, Path(dest))
            self.current = None
            self.refresh()
            self.status.setText(f"Moved to project: {target.name} -> {target.parent}")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _confirm_unrenamed(self) -> bool:
        if load_skip_rename_warning():
            return True
        if not is_default_obs_name(self.current.stem):
            return True
        box = QMessageBox(self)
        box.setWindowTitle("Save to Project")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText("This recording hasn't been renamed.")
        box.setInformativeText(
            f"'{self.current.name}' still has its default OBS name.\n"
            "Save it to a project anyway?"
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)
        checkbox = QCheckBox("Do not ask again")
        box.setCheckBox(checkbox)
        result = box.exec()
        if checkbox.isChecked():
            save_skip_rename_warning(True)
        return result == QMessageBox.StandardButton.Yes

    def refresh(self):
        files = scan_folder(self.folder)
        self.last_snapshot = {str(p) for p in files}
        self.recording_list.load(files)
        if files:
            self.select_path(files[0])
        else:
            self.current = None
            self.status.setText("No video recordings found.")
            self.name_edit.clear()

    def _check_for_new(self):
        newest = detect_new_files(self.folder, self.last_snapshot)
        files = scan_folder(self.folder)
        self.last_snapshot = {str(p) for p in files}
        if newest:
            self.refresh()
            self.select_path(newest)

    def _on_item_clicked(self, item):
        self.select_path(self.recording_list.path_for_item(item))

    def select_path(self, path):
        if not path.exists():
            return
        self.current = path
        self.name_edit.setText(path.stem)
        self.status.setText(f"Selected: {path.name}")
        self.recording_list.select_path(path)
        self.player.play_file(path)

    def _nav_prev(self):
        self.recording_list.select_prev()
        path = self.recording_list.selected_path()
        if path:
            self.select_path(path)

    def _nav_next(self):
        self.recording_list.select_next()
        path = self.recording_list.selected_path()
        if path:
            self.select_path(path)

    def delete_current(self):
        if not self.current or not self.current.exists():
            return
        path = self.current
        reply = QMessageBox.question(
            self,
            "Delete recording",
            f"Move this file to the Recycle Bin?\n\n{path.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.player.unload()
        try:
            delete_file(path)
            self.current = None
            self.refresh()
            self.status.setText(f"Moved to Recycle Bin: {path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))

    def rename_current(self):
        if not self.current or not self.current.exists():
            return
        new_stem = self.name_edit.text().strip()
        if not new_stem:
            QMessageBox.warning(self, "Rename", "Enter a name first.")
            return
        try:
            self.player.unload()
            target = rename_file(self.current, new_stem)
            self.current = target
            self.name_edit.setText(target.stem)
            self.refresh()
            self.status.setText(f"Renamed to: {target.name}")
        except ValueError as e:
            QMessageBox.warning(self, "Rename", str(e))
            self.player.play_file(self.current)
        except FileExistsError as e:
            QMessageBox.warning(self, "Rename", str(e))
            self.player.play_file(self.current)
        except Exception as e:
            QMessageBox.critical(self, "Rename failed", str(e))
