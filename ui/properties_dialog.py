import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QGroupBox, QPlainTextEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QInputDialog
)

class PropertiesDialog(QDialog):
    """Dialog for editing website properties (title, notes, etc.)"""
    def __init__(self, parent, db_manager, website, on_save=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.website = website
        self.on_save = on_save
        
        self.setWindowTitle("Edit Properties")
        self.resize(500, 400)
        
        self.title_var = website['title']
        self._init_ui()
        self._load_notes()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        props_group = QGroupBox("Properties")
        props_layout = QHBoxLayout()
        props_group.setLayout(props_layout)
        
        label_title = QLabel("Title:")
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.title_var)
        
        props_layout.addWidget(label_title)
        props_layout.addWidget(self.title_edit, 1)
        
        main_layout.addWidget(props_group)
        
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)
        
        info_layout.addWidget(QLabel(f"URL: {self.website['url']}"))
        info_layout.addWidget(QLabel(f"Domain: {self.website['domain']}"))
        info_layout.addWidget(QLabel(f"Date saved: {self.website['date_saved']}"))
        info_layout.addWidget(QLabel(f"Directory: {self.website['directory']}"))
        
        main_layout.addWidget(info_group)
        
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        notes_group.setLayout(notes_layout)
        
        self.notes_text = QPlainTextEdit()
        notes_layout.addWidget(self.notes_text, 1)
        
        add_note_btn = QPushButton("Add Note")
        add_note_btn.clicked.connect(self._add_note)
        notes_layout.addWidget(add_note_btn)
        
        main_layout.addWidget(notes_group, 1)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._save_properties)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)
    
    def _load_notes(self):
        notes = self.db_manager.get_website_notes(self.website['id'])
        self.notes_text.clear()
        for n in notes:
            date_str = str(n["date_created"]).split('.')[0]
            self.notes_text.appendPlainText(f"[{date_str}] {n['note']}\n")
    
    def _add_note(self):
        text, ok = QInputDialog.getText(self, "Add Note", "Enter a note:")
        if ok and text.strip():
            self.db_manager.add_note(self.website['id'], text.strip())
            self._load_notes()
    
    def _save_properties(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Warning", "Title cannot be empty")
            return
        updates = {"title": title}
        self.db_manager.update_website(self.website["id"], updates)
        
        # update metadata.json
        try:
            meta_path = os.path.join(self.website["directory"], "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                meta["title"] = title
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, indent=4)
        except Exception as e:
            print(f"Error updating metadata.json: {e}")
        
        self.accept()
        if self.on_save:
            self.on_save()