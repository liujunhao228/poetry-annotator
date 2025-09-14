# gui/config_panels/plugins_config_panel.py
# Panel for managing project plugin configurations.

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QWidget,
    QFormLayout,
    QCheckBox
)
from ..i18n import _
from ..config_manager import ConfigHandler

class PluginsConfigPanel(QDialog):
    """
    A dialog for managing project plugin configurations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Plugin Configuration"))
        self.setGeometry(200, 200, 800, 600)
        self.config_handler = ConfigHandler()
        self.plugins_config = self.config_handler.get_plugins_config()
        self.checkboxes = {}
        self._setup_ui()
        self._load_plugins()

    def _setup_ui(self):
        """
        Sets up the UI components of the dialog.
        """
        self.main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)

        container = QWidget()
        self.form_layout = QFormLayout(container)
        scroll_area.setWidget(container)

        # Save and Close buttons
        button_layout = QVBoxLayout()
        self.save_button = QPushButton(_("Save"))
        self.save_button.clicked.connect(self.save_config)
        self.close_button = QPushButton(_("Close"))
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        
        self.main_layout.addLayout(button_layout)

    def _load_plugins(self):
        """
        Loads the plugins into the form layout.
        """
        for plugin_name, plugin_config in self.plugins_config.items():
            is_enabled = plugin_config.get("enabled", "false").lower() == "true"
            checkbox = QCheckBox(plugin_name)
            checkbox.setChecked(is_enabled)
            self.form_layout.addRow(checkbox)
            self.checkboxes[plugin_name] = checkbox

    def save_config(self):
        """
        Saves the plugin configurations.
        """
        for plugin_name, checkbox in self.checkboxes.items():
            self.plugins_config[plugin_name]["enabled"] = str(checkbox.isChecked()).lower()

        if self.config_handler.save_plugins_config(self.plugins_config):
            QMessageBox.information(self, _("Save Configuration"), _("Configuration saved successfully!"))
            self.accept()
        else:
            QMessageBox.critical(self, _("Error"), _("Failed to save configuration."))