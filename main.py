# """
# Entry point for PowerPulse
# """
# from ui.main_window import run_app

# if __name__ == "__main__":
#     run_app()

from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
