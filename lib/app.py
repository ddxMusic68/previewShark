import sys
from PySide6.QtWidgets import QApplication
from lib.widgets.main_window import MainWindow


def main() -> int:
    app = QApplication([])
    app.setApplicationName("Take Reviewer")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())