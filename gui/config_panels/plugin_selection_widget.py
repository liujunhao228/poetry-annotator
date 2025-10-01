# gui/config_panels/plugin_selection_widget.py
# Implements a reusable widget for selecting and managing project plugins.

import logging
import gettext
from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QCheckBox, QGroupBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from ..config_manager import ConfigHandler
from src.config.schema import ProjectPluginsConfig, PluginConfig

_ = gettext.gettext

class PluginSelectionWidget(QWidget):
    """
    A reusable widget for selecting and managing project plugins.
    It displays a list of available plugins with checkboxes to enable/disable them.
    """
    # Signal emitted when the plugin selection changes
    plugins_changed = pyqtSignal(dict) # Emits a dict of {plugin_name: enabled_status}

    def __init__(self, config_handler: ConfigHandler, parent=None):
        super().__init__(parent)
        self.config_handler = config_handler
        self._plugin_checkboxes = {} # To store references to plugin checkboxes
        self._setup_ui()
        self._load_plugin_states() # Initial population

    def _setup_ui(self):
        """
        Sets up the UI for the plugin selection widget.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        plugins_group_box = QGroupBox(_("Project Plugins"))
        plugins_layout = QFormLayout(plugins_group_box)
        plugins_layout.setLabelAlignment(Qt.AlignRight)
        plugins_layout.setHorizontalSpacing(15)
        plugins_layout.setVerticalSpacing(10)

        self._build_plugin_form(plugins_layout)
        main_layout.addWidget(plugins_group_box)

    def _build_plugin_form(self, parent_layout: QFormLayout):
        """
        Builds the form layout specifically for plugins.
        """
        project_plugins_config = self.config_handler.get_plugins_config()
        if project_plugins_config and project_plugins_config.plugins:
            for plugin_name in sorted(project_plugins_config.plugins.keys()):
                checkbox = QCheckBox(plugin_name)
                checkbox.stateChanged.connect(self._on_plugin_state_changed)
                parent_layout.addRow(checkbox)
                self._plugin_checkboxes[plugin_name] = checkbox
        else:
            no_plugins_label = QLabel(_("No plugins available."))
            parent_layout.addRow(no_plugins_label)

    def _load_plugin_states(self):
        """
        Loads the current plugin states from the config handler into the UI.
        """
        current_project_config = self.config_handler.get_project_config()
        if current_project_config and current_project_config.plugins:
            for plugin_name, checkbox in self._plugin_checkboxes.items():
                plugin_config: Optional[PluginConfig] = current_project_config.plugins.plugins.get(plugin_name)
                if plugin_config:
                    checkbox.setChecked(plugin_config.enabled)
                else:
                    # If plugin not explicitly in project config, assume enabled by default
                    checkbox.setChecked(True)
        else:
            # If no project config or no plugin section, all checkboxes should be checked (default enabled)
            for checkbox in self._plugin_checkboxes.values():
                checkbox.setChecked(True)

    def get_plugin_states(self) -> Dict[str, bool]:
        """
        Retrieves the current enabled/disabled state of all plugins from the UI.
        """
        states = {}
        for plugin_name, checkbox in self._plugin_checkboxes.items():
            states[plugin_name] = checkbox.isChecked()
        return states

    def set_plugin_states(self, plugin_states: Dict[str, bool]):
        """
        Sets the plugin states in the UI based on the provided dictionary.
        """
        for plugin_name, enabled in plugin_states.items():
            if plugin_name in self._plugin_checkboxes:
                self._plugin_checkboxes[plugin_name].setChecked(enabled)
        self._emit_plugins_changed()

    def _on_plugin_state_changed(self, state: int):
        """
        Slot to handle state changes of plugin checkboxes.
        Emits the plugins_changed signal.
        """
        self._emit_plugins_changed()

    def _emit_plugins_changed(self):
        """Emits the signal when plugin states change."""
        self.plugins_changed.emit(self.get_plugin_states())
