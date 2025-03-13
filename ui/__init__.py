# UI components for the Website Archiver
"""
This package contains all PyQt6-based dialogs and windows for the application.

The UI components handle user interaction, display archived websites,
and provide interfaces for downloading, editing, and managing website data.
"""

from .main_window import MainWindow
from .editor_dialog import WebsiteEditorDialog
from .tag_dialog import TagManagerDialog
from .properties_dialog import PropertiesDialog

__all__ = [
    'MainWindow', 
    'WebsiteEditorDialog', 
    'TagManagerDialog', 
    'PropertiesDialog'
]