from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QDialogButtonBox
)

class TagManagerDialog(QDialog):
    """Dialog for managing tags for a website"""
    def __init__(self, parent, db_manager, website_id):
        super().__init__(parent)
        self.db_manager = db_manager
        self.website_id = website_id
        
        self.setWindowTitle("Manage Tags")
        self.resize(400, 400)
        
        self.tag_list = []
        self.suggestion_list = []
        
        self._init_ui()
        self._load_tags()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        main_layout.addWidget(QLabel("Current Tags:"))
        self.current_tags_layout = QHBoxLayout()
        main_layout.addLayout(self.current_tags_layout)
        
        main_layout.addSpacing(10)
        
        add_layout = QHBoxLayout()
        self.tag_edit = QLineEdit()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_tag)
        add_layout.addWidget(QLabel("Add Tag:"))
        add_layout.addWidget(self.tag_edit, 1)
        add_layout.addWidget(add_btn)
        main_layout.addLayout(add_layout)
        
        main_layout.addSpacing(10)
        
        main_layout.addWidget(QLabel("Suggestions:"))
        self.suggestions_layout = QHBoxLayout()
        main_layout.addLayout(self.suggestions_layout)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)
    
    def _load_tags(self):
        self.tag_list = self.db_manager.get_website_tags(self.website_id)
        self._update_current_tags()
        
        all_tags = self.db_manager.get_all_tags()
        current_ids = [t["id"] for t in self.tag_list]
        self.suggestion_list = [t for t in all_tags if t["id"] not in current_ids]
        self._update_suggestions()
    
    def _update_current_tags(self):
        # Clear layout
        for i in reversed(range(self.current_tags_layout.count())):
            w = self.current_tags_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        
        if not self.tag_list:
            self.current_tags_layout.addWidget(QLabel("No tags assigned"))
            return
        
        for t in self.tag_list:
            btn = QPushButton(f"✕ {t['name']}")
            btn.clicked.connect(lambda _, tag=t: self._remove_tag(tag))
            self.current_tags_layout.addWidget(btn)
    
    def _update_suggestions(self):
        for i in reversed(range(self.suggestions_layout.count())):
            w = self.suggestions_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        
        if not self.suggestion_list:
            self.suggestions_layout.addWidget(QLabel("No suggestions available"))
            return
        
        for t in self.suggestion_list:
            btn = QPushButton(f"{t['name']} ({t['count']})")
            btn.clicked.connect(lambda _, tag=t: self._add_existing_tag(tag))
            self.suggestions_layout.addWidget(btn)
    
    def _add_tag(self):
        tag_name = self.tag_edit.text().strip()
        if not tag_name:
            return
        success = self.db_manager.add_website_tag(self.website_id, tag_name)
        if success:
            self.tag_edit.clear()
            self._load_tags()
    
    def _add_existing_tag(self, tag):
        success = self.db_manager.add_website_tag(self.website_id, tag["name"])
        if success:
            self._load_tags()
    
    def _remove_tag(self, tag):
        self.db_manager.remove_website_tag(self.website_id, tag["id"])
        self._load_tags()