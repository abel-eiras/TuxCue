import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.audio.engine import AudioEngine
from src.config import load as load_config
from src.core.audio_controller import AudioController
from src.gui.main_window import MainWindow
from src.i18n import set_locale

_ICON = Path(__file__).parent / "docs" / "icon.png"


def main() -> None:
    config = load_config()
    set_locale(str(config.get("language", "es")))

    app = QApplication(sys.argv)
    if _ICON.exists():
        app.setWindowIcon(QIcon(str(_ICON)))

    engine = AudioEngine()
    controller = AudioController(engine=engine)
    window = MainWindow(controller=controller)
    window.setWindowTitle("TuxCue")
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
