import sys
from PySide6.QtWidgets import QApplication
from lib.widgets.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationName("Take Reviewer")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
