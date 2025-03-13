#!/usr/bin/env python3
"""
Website Archiver - A program for saving and organizing websites locally.

This module is the entry point of the application and initializes the main window.
"""

import sys
from typing import NoReturn

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> NoReturn:
    """
    Main function of the program.
    
    Initializes the Qt application and main window, then starts the event loop.
    
    Returns:
        NoReturn: This function does not return as it enters the Qt event loop.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()