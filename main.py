import sys

from PySide6.QtWidgets import QApplication

from src.audio.engine import AudioEngine
from src.config import load as load_config
from src.core.audio_controller import AudioController
from src.gui.main_window import MainWindow
from src.i18n import set_locale


def main() -> None:
    config = load_config()
    set_locale(str(config.get("language", "es")))

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
