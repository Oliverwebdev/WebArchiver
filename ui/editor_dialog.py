import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QWidget, QListWidget, QPlainTextEdit, QMessageBox,
    QInputDialog
)

from .tag_dialog import TagManagerDialog
from .properties_dialog import PropertiesDialog

class WebsiteEditorDialog(QDialog):
    """
    Dialog for editing a saved website: listing files (HTML, CSS, JS, metadata),
    editing their content, etc.
    """
    def __init__(self, parent, metadata, db_manager, storage, on_save=None):
        super().__init__(parent)
        self.metadata = metadata
        self.db_manager = db_manager
        self.storage = storage
        self.on_save = on_save
        
        self.setWindowTitle(f"Edit Website - {metadata['title']}")
        self.resize(1000, 700)
        
        self.file_list = []
        self.current_file_path = None
        self.modified = False
        
        self._init_ui()
        self._load_website_files()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Buttons: Save, Save as new website, Manage Tags, Edit Properties
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_file)
        btn_layout.addWidget(self.save_btn)
        
        self.save_as_new_btn = QPushButton("Save As New Website")
        self.save_as_new_btn.clicked.connect(self._save_as_new_website)
        btn_layout.addWidget(self.save_as_new_btn)
        
        tag_btn = QPushButton("Manage Tags")
        tag_btn.clicked.connect(self._manage_tags)
        btn_layout.addWidget(tag_btn)
        
        prop_btn = QPushButton("Edit Properties")
        prop_btn.clicked.connect(self._edit_properties)
        btn_layout.addWidget(prop_btn)
        
        # Splitter: left file list, right text editor
        splitter = QSplitter(self)
        main_layout.addWidget(splitter, 1)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.file_list_widget = QListWidget()
        self.file_list_widget.itemSelectionChanged.connect(self._on_file_selected)
        left_layout.addWidget(QLabel("Files:"))
        left_layout.addWidget(self.file_list_widget, 1)
        
        splitter.addWidget(left_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.file_label = QLabel("No file selected")
        right_layout.addWidget(self.file_label)
        
        self.editor = QPlainTextEdit()
        self.editor.textChanged.connect(self._mark_as_modified)
        right_layout.addWidget(self.editor, 1)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
    
    def _load_website_files(self):
        dir_path = self.metadata["directory"]
        self.file_list.clear()
        
        # index.html
        html_file = os.path.join(dir_path, "index.html")
        if os.path.exists(html_file):
            self.file_list.append(("HTML: index.html", html_file))
        
        # CSS
        css_dir = os.path.join(dir_path, "assets", "css")
        if os.path.exists(css_dir):
            for f in os.listdir(css_dir):
                if f.endswith(".css"):
                    path_ = os.path.join(css_dir, f)
                    self.file_list.append((f"CSS: {f}", path_))
        
        # JS
        js_dir = os.path.join(dir_path, "assets", "js")
        if os.path.exists(js_dir):
            for f in os.listdir(js_dir):
                if f.endswith(".js"):
                    path_ = os.path.join(js_dir, f)
                    self.file_list.append((f"JS: {f}", path_))
        
        # metadata.json
        metadata_file = os.path.join(dir_path, "metadata.json")
        if os.path.exists(metadata_file):
            self.file_list.append(("Metadata: metadata.json", metadata_file))
        
        self.file_list_widget.clear()
        for label, _ in self.file_list:
            self.file_list_widget.addItem(label)
    
    def _on_file_selected(self):
        if self.current_file_path and self.modified:
            ret = QMessageBox.question(self, "Save Changes",
                                       f"Save changes to {self.current_file_path}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.Yes:
                self._save_file()
        
        items = self.file_list_widget.selectedItems()
        if not items:
            return
        selected_label = items[0].text()
        # find corresponding path
        for label, path_ in self.file_list:
            if label == selected_label:
                self.current_file_path = path_
                break
        
        self.file_label.setText(selected_label)
        
        try:
            with open(self.current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.modified = False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def _mark_as_modified(self):
        if self.current_file_path:
            self.modified = True
    
    def _save_file(self):
        if not self.current_file_path:
            return
        try:
            content = self.editor.toPlainText()
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.modified = False
            QMessageBox.information(self, "Saved", f"File saved: {self.current_file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")
    
    def _save_as_new_website(self):
        if self.current_file_path and self.modified:
            self._save_file()
        
        new_name, ok = QInputDialog.getText(self, "Save As New Website",
                                            "Enter a name for the new website:",
                                            text=f"{self.metadata['title']} (edited)")
        if not ok or not new_name.strip():
            return
        
        try:
            new_metadata = self.storage.create_new_version(self.metadata["directory"], new_name.strip())
            website_id = self.db_manager.add_website(new_metadata)
            if website_id:
                original = self.db_manager.get_website_by_directory(self.metadata["directory"])
                if original:
                    original_tags = self.db_manager.get_website_tags(original["id"])
                    for t in original_tags:
                        self.db_manager.add_website_tag(website_id, t["name"])
            QMessageBox.information(self, "Saved",
                                    f"Website saved as new version:\n{new_name}\n\nCheck it in the home tab.")
            self.close()
            if self.on_save:
                self.on_save()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving as new website: {str(e)}")
    
    def _manage_tags(self):
        website = self.db_manager.get_website_by_directory(self.metadata["directory"])
        if not website:
            QMessageBox.information(self, "Info",
                                    "This website is not in the database yet. Save it as a new version first.")
            return
        dlg = TagManagerDialog(self, self.db_manager, website["id"])
        dlg.exec()
    
    def _edit_properties(self):
        website = self.db_manager.get_website_by_directory(self.metadata["directory"])
        if not website:
            QMessageBox.information(self, "Info",
                                    "This website is not in the database yet. Save it as a new version first.")
            return
        dlg = PropertiesDialog(self, self.db_manager, website, self.on_save)
        dlg.exec()