from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class RecordingList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path: Path | None = None

    def load(self, files: list[Path]):
        self.clear()
        for p in files:
            item = QListWidgetItem(p.name)
            item.setData(Qt.ItemDataRole.UserRole, str(p))
            self.addItem(item)

    def path_for_item(self, item: QListWidgetItem) -> Path:
        return Path(item.data(Qt.ItemDataRole.UserRole))

    def select_path(self, path: Path):
        for i in range(self.count()):
            item = self.item(i)
            if self.path_for_item(item) == path:
                self.setCurrentItem(item)
                self.current_path = path
                return

    def selected_path(self) -> Path | None:
        item = self.currentItem()
        if item is None:
            return None
        return self.path_for_item(item)

    def select_prev(self):
        row = self.currentRow()
        if row > 0:
            self.setCurrentRow(row - 1)

    def select_next(self):
        row = self.currentRow()
        if row < self.count() - 1:
            self.setCurrentRow(row + 1)
