"""Belépési pont: a Slice Designer GUI önálló elindítása."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from slicedesigner.gui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> None:
    """`QApplication` és `MainWindow` létrehozása, majd az alkalmazás indítása."""
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logger.info("Slice Designer GUI elindítva.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
