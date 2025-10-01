# gui/main_window.py
# Defines the MainWindow class, inheriting from QMainWindow.
# This will be the main application window, managing tabs for different script panels.

import logging
import os
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QVBoxLayout, QWidget, QTextEdit, QMenuBar, QAction, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from .utils import LogStreamHandler
from .config_panels.global_config_panel import GlobalConfigPanel
from .config_panels.project_config_panel import ProjectConfigPanel
from .config_manager import ConfigHandler
from .i18n import _
from .styles import get_stylesheet

class MainWindow(QMainWindow):
    """
    The main application window, inheriting from QMainWindow.
    Manages tabs for different script panels and displays global status/logs.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Poetry Annotator GUI"))
        self.setGeometry(100, 100, 1200, 800) # Initial window size
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'app_icon.txt')  # Using the placeholder file
        if os.path.exists(icon_path):
            # In a real application, this would be an actual icon file
            # self.setWindowIcon(QIcon(icon_path))
            pass

        self._setup_ui()
        self._setup_logging()
        self.config_handler = ConfigHandler()
        # Initial update will be triggered from app.py after panels are added

    def _setup_ui(self):
        """
        Sets up the main window's UI components: tab widget, status bar, menu bar, and log display.
        """
        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())
        
        # Central Widget and Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Tab Widget for Script Panels
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(_("Ready"))

        # Menu Bar
        self._setup_menu_bar()

        # Global Log Display (optional, as per design, but useful for debugging)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150) # Limit height of log display
        self.main_layout.addWidget(self.log_display)

    def _setup_menu_bar(self):
        """
        Sets up the application's menu bar.
        """
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu(_("&File"))
        exit_action = QAction(_("E&xit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip(_("Exit application"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings Menu (will be expanded in Phase 3)
        settings_menu = menu_bar.addMenu(_("&Settings"))
        
        global_config_action = QAction(_("Edit &Global Configuration"), self)
        global_config_action.triggered.connect(self._open_global_config)
        settings_menu.addAction(global_config_action)

        project_config_action = QAction(_("Edit &Project Configuration"), self)
        project_config_action.triggered.connect(self._open_project_config)
        settings_menu.addAction(project_config_action)

        llm_config_action = QAction(_("Edit &LLM Configuration"), self)
        llm_config_action.triggered.connect(self._open_llm_config)
        settings_menu.addAction(llm_config_action)

        # Help Menu
        help_menu = menu_bar.addMenu(_("&Help"))
        about_action = QAction(_("&About"), self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _setup_logging(self):
        """
        Sets up the global logging handler to redirect output to the GUI.
        """
        self.log_handler = LogStreamHandler()
        self.log_handler.log_signal.connect(self._update_log_display)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.DEBUG) # Set logging level to DEBUG for detailed output

        logging.info(_("GUI application started."))

    def _update_log_display(self, message: str):
        """
        Slot to receive log messages and display them in the QTextEdit.
        """
        self.log_display.append(message)

    def add_script_panel(self, panel: QWidget, title: str):
        """
        Adds a script panel as a new tab to the QTabWidget.
        """
        self.tab_widget.addTab(panel, title)
        logging.info(_("Added script panel: {}").format(title))

    def _open_global_config(self):
        """Opens the global configuration panel."""
        global_config_dialog = GlobalConfigPanel(self)
        global_config_dialog.config_saved.connect(self._on_config_saved)
        global_config_dialog.exec_()
        logging.info(_("Global configuration panel opened."))

    def _open_project_config(self):
        """Opens the project configuration panel."""
        project_config_dialog = ProjectConfigPanel(self)
        project_config_dialog.config_saved.connect(self._on_config_saved)
        project_config_dialog.project_switched.connect(self._on_project_switched)
        project_config_dialog.exec_()
        logging.info(_("Project configuration panel opened."))

    def _on_config_saved(self):
        """Handles actions after a configuration is saved."""
        self.status_bar.showMessage(_("Configuration saved successfully!"))
        logging.info(_("Configuration saved signal received."))

    def _on_project_switched(self, project_name: str):
        """Handles actions after a project is switched."""
        self.status_bar.showMessage(_("Switched to project: {}").format(project_name))
        logging.info(_("Project switched to: {}").format(project_name))
        self._update_panels_with_project_config()

    def _update_panels_with_project_config(self):
        """
        Updates all script panels with the current project's configuration,
        such as the database name.
        """
        db_name = self.config_handler.get_database_name()
        if db_name:
            for i in range(self.tab_widget.count()):
                panel = self.tab_widget.widget(i)
                if hasattr(panel, 'update_database_name'):
                    panel.update_database_name(db_name)

    def _open_llm_config(self):
        logging.info(_("LLM configuration panel opened."))

    def _show_about_dialog(self):
        """Displays an about dialog."""
        QMessageBox.about(self, _("About Poetry Annotator GUI"),
                          _("Poetry Annotator GUI\n\nVersion 1.0\n\n"
                            "A graphical user interface for managing poetry annotation tasks."))
        logging.info(_("Displayed about dialog."))

    def closeEvent(self, event):
        """
        Handles the close event for the main window.
        """
        logging.info(_("GUI application closing."))
        # Clean up logging handler if necessary
        logging.getLogger().removeHandler(self.log_handler)
        super().closeEvent(event)
