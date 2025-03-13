import os
import sys
import shutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QPushButton, QLineEdit, QMessageBox,
    QComboBox, QCheckBox, QScrollArea, QPlainTextEdit, QRadioButton,
    QGroupBox, QGridLayout, QProgressBar, QFileDialog, QStatusBar,
    QFrame, QSpacerItem, QSizePolicy, QSpinBox
)

from .editor_dialog import WebsiteEditorDialog
from session_manager import SessionManager
from scraper import WebArchiver

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

import os
import sys
import shutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QPushButton, QLineEdit, QMessageBox,
    QComboBox, QCheckBox, QScrollArea, QPlainTextEdit, QRadioButton,
    QGroupBox, QGridLayout, QProgressBar, QFileDialog, QStatusBar,
    QFrame, QSpacerItem, QSizePolicy, QSpinBox
)
from PyQt6.QtGui import QPixmap, QFont

from .editor_dialog import WebsiteEditorDialog
from session_manager import SessionManager
from scraper import WebArchiver

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Website Archiver (PyQt6)")
        self.resize(1000, 700)
        
        self.archiver = WebArchiver()
        self.session = SessionManager()
        
        # UI state
        self.url_var = ""
        self.search_var = ""
        
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        
        self._init_ui()
        self.load_saved_websites()
        self._restore_session()
    
    def _init_ui(self):
        # Central widget with tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add logo at the top
        logo_layout = QHBoxLayout()
        main_layout.addLayout(logo_layout)
        
        # Add a spacer on the left
        logo_layout.addStretch(1)
        
        # Add logo image
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "WebArchiver.jpg")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # Scale the logo to an appropriate size (e.g., 150px wide, keeping aspect ratio)
            logo_pixmap = logo_pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_layout.addWidget(logo_label)
        
        # Add app title next to the logo
        title_label = QLabel("Website Archiver")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        logo_layout.addWidget(title_label)
        
        # Add a spacer on the right
        logo_layout.addStretch(1)
        
        # Add a horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)
        
        # Create tabs
        self.home_tab = QWidget()
        self.download_tab = QWidget()
        self.batch_tab = QWidget()
        self.settings_tab = QWidget()
        
        self.tabs.addTab(self.home_tab, "Home")
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.batch_tab, "Batch Download")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Build each tab
        self._setup_home_tab()
        self._setup_download_tab()
        self._setup_batch_tab()
        self._setup_settings_tab()
        
        # Status bar at bottom
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.addWidget(self.status_label)
        status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.setValue(0)
        
        # Tab change event
        self.tabs.currentChanged.connect(self._on_tab_changed)
    
    # -------------- Home Tab --------------
    def _setup_home_tab(self):
        layout = QVBoxLayout(self.home_tab)
        
        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        
        # search
        search_box = QHBoxLayout()
        top_layout.addLayout(search_box, 1)
        
        search_box.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._filter_websites)
        search_box.addWidget(self.search_edit, 1)
        
        # tag filter
        tag_box = QHBoxLayout()
        top_layout.addLayout(tag_box)
        
        tag_box.addWidget(QLabel("Tag:"))
        self.tag_combobox = QComboBox()
        self.tag_combobox.currentIndexChanged.connect(lambda _: self._filter_websites())
        tag_box.addWidget(self.tag_combobox)
        
        # refresh & import
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_saved_websites)
        top_layout.addWidget(refresh_btn)
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self._import_website)
        top_layout.addWidget(import_btn)
        
        # scroll area for "cards"
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        layout.addWidget(self.cards_scroll, 1)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_scroll.setWidget(self.cards_container)
        
    # -------------- Download Tab --------------
    def _setup_download_tab(self):
        layout = QVBoxLayout(self.download_tab)
        
        url_layout = QHBoxLayout()
        layout.addLayout(url_layout)
        
        url_layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit()
        url_layout.addWidget(self.url_edit, 1)
        
        dl_btn = QPushButton("Download")
        dl_btn.clicked.connect(self._download_website)
        url_layout.addWidget(dl_btn)
        
        # Recent URLs
        recent_box = QGroupBox("Recent URLs")
        layout.addWidget(recent_box)
        vbox_recent = QVBoxLayout(recent_box)
        self.recent_urls_layout = QVBoxLayout()
        vbox_recent.addLayout(self.recent_urls_layout)
        
        # Download options
        opt_box = QGroupBox("Download Options")
        layout.addWidget(opt_box)
        opt_layout = QVBoxLayout(opt_box)
        
        # engine
        engine_group = QGroupBox("Engine")
        eg_layout = QVBoxLayout(engine_group)
        self.radio_requests = QRadioButton("Standard (requests)")
        self.radio_selenium = QRadioButton("Selenium")
        self.radio_playwright = QRadioButton("Playwright (if installed)")
        self.radio_requests.setChecked(True)
        
        eg_layout.addWidget(self.radio_requests)
        eg_layout.addWidget(self.radio_selenium)
        if PLAYWRIGHT_AVAILABLE:
            eg_layout.addWidget(self.radio_playwright)
        opt_layout.addWidget(engine_group)
        
        # resource checkboxes
        resource_layout = QGridLayout()
        self.chk_images = QCheckBox("Download Images")
        self.chk_css = QCheckBox("Download CSS")
        self.chk_js = QCheckBox("Download JS")
        self.chk_fonts = QCheckBox("Download Fonts")
        
        self.chk_images.setChecked(self.archiver.config_manager.get("download_images", True))
        self.chk_css.setChecked(self.archiver.config_manager.get("download_css", True))
        self.chk_js.setChecked(self.archiver.config_manager.get("download_js", True))
        self.chk_fonts.setChecked(self.archiver.config_manager.get("download_fonts", True))
        
        resource_layout.addWidget(self.chk_images, 0, 0)
        resource_layout.addWidget(self.chk_css, 0, 1)
        resource_layout.addWidget(self.chk_js, 0, 2)
        resource_layout.addWidget(self.chk_fonts, 0, 3)
        
        opt_layout.addLayout(resource_layout)
        
        layout.addStretch()
    
    # -------------- Batch Tab --------------
    def _setup_batch_tab(self):
        layout = QVBoxLayout(self.batch_tab)
        layout.addWidget(QLabel("Enter multiple URLs (one per line):"))
        
        self.batch_edit = QPlainTextEdit()
        layout.addWidget(self.batch_edit, 1)
        
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)
        
        start_btn = QPushButton("Start Batch Download")
        start_btn.clicked.connect(self._start_batch_download)
        btn_layout.addStretch(1)
        btn_layout.addWidget(start_btn)
        
        last_batch = self.session.get_batch_urls()
        if last_batch:
            self.batch_edit.setPlainText(last_batch)
    
    # -------------- Settings Tab --------------
    def _setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        
        form_layout = QGridLayout()
        layout.addLayout(form_layout)
        
        form_layout.addWidget(QLabel("Base Directory:"), 0, 0)
        self.base_dir_edit = QLineEdit(self.archiver.config_manager.get("base_dir"))
        form_layout.addWidget(self.base_dir_edit, 0, 1)
        
        form_layout.addWidget(QLabel("Max Concurrent Downloads:"), 1, 0)
        self.spin_max_concurrent = QSpinBox()
        self.spin_max_concurrent.setRange(1, 1000)
        self.spin_max_concurrent.setValue(self.archiver.config_manager.get("max_concurrent_downloads", 8))
        form_layout.addWidget(self.spin_max_concurrent, 1, 1)
        
        form_layout.addWidget(QLabel("Timeout (seconds):"), 2, 0)
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(1, 9999)
        self.spin_timeout.setValue(self.archiver.config_manager.get("timeout", 30))
        form_layout.addWidget(self.spin_timeout, 2, 1)
        
        self.chk_robots = QCheckBox("Respect robots.txt")
        self.chk_robots.setChecked(self.archiver.config_manager.get("respect_robots_txt", True))
        form_layout.addWidget(self.chk_robots, 3, 0)
        
        self.chk_sanitize = QCheckBox("Sanitize HTML")
        self.chk_sanitize.setChecked(self.archiver.config_manager.get("sanitize_html", False))
        form_layout.addWidget(self.chk_sanitize, 3, 1)
        
        form_layout.addWidget(QLabel("User Agent:"), 4, 0)
        self.user_agent_edit = QLineEdit(self.archiver.config_manager.get("user_agent", "WebArchiver/2.0"))
        form_layout.addWidget(self.user_agent_edit, 4, 1)
        
        self.chk_headless = QCheckBox("Selenium Headless Mode")
        self.chk_headless.setChecked(self.archiver.config_manager.get("selenium_headless", True))
        form_layout.addWidget(self.chk_headless, 5, 0)
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
    
    # --------------------------------------------------------------------------------
    #                               Home Tab Support
    # --------------------------------------------------------------------------------
    def load_saved_websites(self):
        self.current_sites = self.archiver.get_all_websites()
        self._display_websites(self.current_sites)
        self._load_tags()
    
    def _load_tags(self):
        tags = self.archiver.db_manager.get_all_tags()
        tag_names = [t["name"] for t in tags]
        self.tag_combobox.clear()
        self.tag_combobox.addItem("")
        for name in tag_names:
            self.tag_combobox.addItem(name)
    
    def _filter_websites(self):
        term = self.search_edit.text().strip()
        tag = self.tag_combobox.currentText().strip()
        if not tag:
            tag = None
        self.current_sites = self.archiver.get_all_websites(search_term=term, tag=tag)
        self._display_websites(self.current_sites)
    
    def _display_websites(self, websites):
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)
        
        for site in websites:
            card_frame = QFrame()
            card_frame.setFrameShape(QFrame.Shape.Panel)
            card_frame.setFrameShadow(QFrame.Shadow.Raised)
            card_layout = QVBoxLayout(card_frame)
            
            top_hbox = QHBoxLayout()
            card_layout.addLayout(top_hbox)
            
            title_lbl = QLabel(f"{site['title']}")
            font = title_lbl.font()
            font.setBold(True)
            title_lbl.setFont(font)
            top_hbox.addWidget(title_lbl, 1)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, s=site: self._edit_website(s))
            top_hbox.addWidget(edit_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, s=site: self._delete_website(s))
            top_hbox.addWidget(delete_btn)
            
            info_lbl = QLabel(f"URL: {site['url']}\nDomain: {site['domain']}\nSaved on: {site['date_saved']}")
            card_layout.addWidget(info_lbl)
            
            self.cards_layout.addWidget(card_frame)
        
        # Add a stretch to push all cards to top
        self.cards_layout.addStretch()
    
    def _delete_website(self, site):
        ret = QMessageBox.question(self, "Delete",
                                   f"Are you sure you want to delete '{site['title']}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            success = self.archiver.delete_website(site["id"], site["directory"])
            if success:
                QMessageBox.information(self, "Deleted", f"'{site['title']}' deleted successfully.")
                self.load_saved_websites()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete website.")
    
    def _edit_website(self, site):
        dlg = WebsiteEditorDialog(self, site, self.archiver.db_manager, self.archiver.scraper,
                                  on_save=self.load_saved_websites)
        dlg.exec()
    
    # --------------------------------------------------------------------------------
    #                               Download Tab Support
    # --------------------------------------------------------------------------------
    def _load_recent_urls(self):
        # Clear existing
        for i in reversed(range(self.recent_urls_layout.count())):
            item = self.recent_urls_layout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)
        
        recent = self.session.get_recent_urls()
        if not recent:
            lbl = QLabel("No recent URLs")
            self.recent_urls_layout.addWidget(lbl)
            return
        
        for url in recent:
            btn = QPushButton(url)
            btn.clicked.connect(lambda _, u=url: self.url_edit.setText(u))
            self.recent_urls_layout.addWidget(btn, 0)
    
    def _download_website(self):
        url = self.url_edit.text().strip()
        if not url:
            return
        self.session.add_recent_url(url)
        self._load_recent_urls()
        
        engine = "requests"
        if self.radio_selenium.isChecked():
            engine = "selenium"
        elif self.radio_playwright.isChecked() and PLAYWRIGHT_AVAILABLE:
            engine = "playwright"
        
        self.archiver.config_manager.set("download_images", self.chk_images.isChecked())
        self.archiver.config_manager.set("download_css", self.chk_css.isChecked())
        self.archiver.config_manager.set("download_js", self.chk_js.isChecked())
        self.archiver.config_manager.set("download_fonts", self.chk_fonts.isChecked())
        
        def progress_callback(message, progress):
            self.status_label.setText(message)
            if progress >= 0:
                self.progress_bar.setValue(progress)
            QApplication.processEvents()
        
        try:
            metadata = self.archiver.download_website(
                url, callback=progress_callback, engine=engine,
                options={
                    "sanitize_html": self.archiver.config_manager.get("sanitize_html"),
                    "ignore_robots_txt": not self.archiver.config_manager.get("respect_robots_txt", True)
                }
            )
            QMessageBox.information(self, "Success",
                                    f"Website downloaded:\n{metadata['title']}")
            self.load_saved_websites()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download failed: {str(e)}")
        finally:
            self.status_label.setText("Ready")
            self.progress_bar.setValue(0)
    
    # --------------------------------------------------------------------------------
    #                               Batch Tab Support
    # --------------------------------------------------------------------------------
    def _start_batch_download(self):
        urls_text = self.batch_edit.toPlainText().strip()
        if not urls_text:
            return
        lines = [l.strip() for l in urls_text.splitlines() if l.strip()]
        if not lines:
            return
        
        self.session.set_batch_urls(urls_text)
        
        engine = "requests"
        if self.radio_selenium.isChecked():
            engine = "selenium"
        elif self.radio_playwright.isChecked() and PLAYWRIGHT_AVAILABLE:
            engine = "playwright"
        
        self.archiver.config_manager.set("download_images", self.chk_images.isChecked())
        self.archiver.config_manager.set("download_css", self.chk_css.isChecked())
        self.archiver.config_manager.set("download_js", self.chk_js.isChecked())
        self.archiver.config_manager.set("download_fonts", self.chk_fonts.isChecked())
        
        def progress_callback(message, progress):
            self.status_label.setText(message)
            if progress >= 0:
                self.progress_bar.setValue(progress)
            QApplication.processEvents()
        
        try:
            result = self.archiver.batch_download(
                lines,
                callback=progress_callback,
                engine=engine,
                options={
                    "sanitize_html": self.archiver.config_manager.get("sanitize_html"),
                    "ignore_robots_txt": not self.archiver.config_manager.get("respect_robots_txt", True)
                }
            )
            summary = (f"Batch download completed.\n"
                       f"Total: {result['total']}\n"
                       f"Successful: {result['successful']}\n"
                       f"Failed: {result['failed']}")
            if result["errors"]:
                errs = "\n".join([f"- {err['url']}: {err['error']}" for err in result["errors"]])
                summary += f"\n\nErrors:\n{errs}"
            QMessageBox.information(self, "Batch Download", summary)
            self.load_saved_websites()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Batch download failed: {str(e)}")
        finally:
            self.status_label.setText("Ready")
            self.progress_bar.setValue(0)
    
    # --------------------------------------------------------------------------------
    #                               Settings Tab Support
    # --------------------------------------------------------------------------------
    def _save_settings(self):
        self.archiver.config_manager.set("base_dir", self.base_dir_edit.text().strip())
        self.archiver.config_manager.set("max_concurrent_downloads", self.spin_max_concurrent.value())
        self.archiver.config_manager.set("timeout", self.spin_timeout.value())
        self.archiver.config_manager.set("respect_robots_txt", self.chk_robots.isChecked())
        self.archiver.config_manager.set("sanitize_html", self.chk_sanitize.isChecked())
        self.archiver.config_manager.set("user_agent", self.user_agent_edit.text().strip())
        self.archiver.config_manager.set("selenium_headless", self.chk_headless.isChecked())
        QMessageBox.information(self, "Settings", "Settings saved successfully.")
    
    # --------------------------------------------------------------------------------
    #                               Import
    # --------------------------------------------------------------------------------
    def _import_website(self):
        dlg = QFileDialog(self, "Select Zip File to Import")
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("Zip Files (*.zip)")
        if dlg.exec() == QFileDialog.DialogCode.Accepted:
            zip_path = dlg.selectedFiles()[0]
            if zip_path:
                try:
                    metadata = self.archiver.import_website(zip_path)
                    QMessageBox.information(self, "Imported",
                                            f"Website imported successfully.\nTitle: {metadata['title']}")
                    self.load_saved_websites()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to import website: {str(e)}")
    
    # --------------------------------------------------------------------------------
    #                               Session / State
    # --------------------------------------------------------------------------------
    def _restore_session(self):
        selected_tab = self.session.get_ui_state("selected_tab", 0)
        if selected_tab < self.tabs.count():
            self.tabs.setCurrentIndex(selected_tab)
        self._load_recent_urls()
    
    def _on_tab_changed(self, idx):
        self.session.set_ui_state("selected_tab", idx)
    
    # --------------------------------------------------------------------------------
    #                                Close
    # --------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.session.save_session()
        super().closeEvent(event)