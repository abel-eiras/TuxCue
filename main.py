import sys

from PySide6.QtWidgets import QApplication

from src.audio.engine import AudioEngine
from src.core.audio_controller import AudioController
from src.gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    engine = AudioEngine()
    controller = AudioController(engine=engine)
    window = MainWindow(controller=controller)
    window.setWindowTitle("TuxCue")
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
