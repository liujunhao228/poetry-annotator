# gui/config_panels/global_config_panel.py
# Implements the GlobalConfigPanel for editing global application configurations.

from typing import Dict, List, Any, Optional, Union
import logging
import gettext
from dataclasses import fields, is_dataclass
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton, QFileDialog, QMessageBox, QComboBox, QScrollArea, QWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
from ..config_manager import ConfigHandler
from ..help_texts import HELP_TEXTS
from ..help_window import HelpWindow
from ..i18n_config import translate_config_key
from src.config.schema import GlobalConfig, GlobalLLMConfig, GlobalDatabaseConfig, \
    GlobalDataPathConfig, GlobalPromptConfig, GlobalLoggingConfig, \
    GlobalVisualizerConfig, GlobalCategoriesConfig, GlobalModelConfigTemplate
import sys # Import sys for float_info

_ = gettext.gettext


def _translate_config_key(k):
    """Translates a configuration key, providing a fallback to a human-readable format."""
    return translate_config_key(k)


class GlobalConfigPanel(QDialog):
    """
    A dialog panel for editing global application configurations.
    Dynamically generates UI based on the GlobalConfig schema.
    """
    config_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Edit Global Configuration"))
        self.setGeometry(200, 200, 800, 600)

        self.config_handler = ConfigHandler()
        self._widgets = {} # To store references to input widgets for dynamic access

        self._setup_ui()
        self._load_config_values()

    def _setup_ui(self):
        """
        Sets up the main layout and dynamically builds the configuration form.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)  # Add spacing between elements
        
        # Add a title for the dialog
        title_label = QLabel(_("Edit Global Configuration"))
        title_label.setProperty("class", "dialog-title")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QFormLayout(self.scroll_content)
        self.form_layout.setLabelAlignment(Qt.AlignRight)  # Right-align labels
        self.form_layout.setHorizontalSpacing(15)  # Add horizontal spacing
        self.form_layout.setVerticalSpacing(10)  # Add vertical spacing
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        self._build_config_form(GlobalConfig, self.form_layout, "Global")

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons
        self.help_button = QPushButton(_("Help"))
        self.help_button.clicked.connect(self._show_help)
        button_layout.addStretch()
        button_layout.addWidget(self.help_button)
        self.save_button = QPushButton(_("Save"))
        self.save_button.clicked.connect(self._save_config_values)
        self.cancel_button = QPushButton(_("Cancel"))
        self.cancel_button.clicked.connect(self.reject) # Closes dialog with reject code
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

    def _build_config_form(self, config_dataclass, parent_layout: QFormLayout, prefix: str):
        """
        Recursively builds the form layout for a given dataclass.
        """
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            if is_dataclass(field_type):
                # Create a group for nested dataclasses
                group_layout = QFormLayout()
                group_label = QLabel(_("<b>%s Settings</b>") % _translate_config_key(field_name))
                parent_layout.addRow(group_label)
                parent_layout.addRow(group_layout)
                self._build_config_form(field_type, group_layout, full_field_name)
            else:
                label = QLabel(_("%s:") % _translate_config_key(field_name))
                widget = self._create_input_widget(field_type, full_field_name)
                if widget:
                    tooltip = HELP_TEXTS.get(full_field_name)
                    if tooltip:
                        label.setToolTip(tooltip)
                        widget.setToolTip(tooltip)
                    parent_layout.addRow(label, widget)
                    self._widgets[full_field_name] = widget
                else:
                    logging.warning(_("No suitable widget for field '%s' of type %s") % (full_field_name, field_type))

    def _show_help(self):
        """
        Displays the centralized help window.
        """
        help_dialog = HelpWindow(self)
        help_dialog.exec_()

    def _create_input_widget(self, field_type, full_field_name: str):
        """
        Creates an appropriate input widget based on the field type.
        """
        # 检查是否是 available_configs 字段，如果是，则创建只读的 QLineEdit
        if (field_type == List[str] or field_type == Optional[List[str]]) and full_field_name.endswith('.available_configs'):
            line_edit = QLineEdit()
            line_edit.setReadOnly(True)  # 设置为只读
            line_edit.setPlaceholderText(_("Defined in configuration file"))
            return line_edit

        if field_type is str:
            return QLineEdit()
        elif field_type is int:
            spin_box = QSpinBox()
            spin_box.setRange(-2147483647, 2147483647) # Max int range
            return spin_box
        elif field_type is float:
            spin_box = QDoubleSpinBox()
            spin_box.setRange(-sys.float_info.max, sys.float_info.max)
            spin_box.setDecimals(3)
            return spin_box
        elif field_type is bool:
            return QCheckBox()
        elif field_type == List[str] or field_type == Optional[List[str]]:
            # For list of strings, use QLineEdit and expect comma-separated values
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(_("Comma-separated values"))
            return line_edit
        elif field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]:
            # For dict of strings, use QLineEdit and expect JSON string
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(_("JSON string (e.g., {\"key\": \"value\"})"))
            return line_edit
        # Add more types as needed (e.g., QComboBox for enums, QFileDialog for paths)
        return None

    def _load_config_values(self):
        """
        Loads current global configuration values into the UI widgets.
        """
        current_config = self.config_handler.get_global_config()
        self._populate_widgets(current_config, "Global")

    def _populate_widgets(self, config_obj, prefix: str):
        """
        Recursively populates widgets with values from a config object.
        """
        for field_info in fields(config_obj):
            field_name = field_info.name
            full_field_name = f"{prefix}.{field_name}"
            value = getattr(config_obj, field_name)

            if is_dataclass(field_info.type):
                self._populate_widgets(value, full_field_name)
            elif full_field_name in self._widgets:
                widget = self._widgets[full_field_name]
                if isinstance(widget, QLineEdit):
                    # 为 available_configs 字段（只读）和其他 List[str] 字段设置文本
                    if field_info.type == List[str] or field_info.type == Optional[List[str]]:
                        widget.setText(", ".join(value) if value else "")
                    elif field_info.type == Dict[str, str] or field_info.type == Optional[Dict[str, str]]:
                        import json
                        widget.setText(json.dumps(value) if value else "")
                    else:
                        widget.setText(str(value) if value is not None else "")
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value) if value is not None else 0)
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value) if value is not None else 0.0)

    def _save_config_values(self):
        """
        Collects values from UI widgets, validates, and saves them via ConfigHandler.
        """
        new_config_data = self._collect_widget_values(GlobalConfig, "Global")
        
        # Basic validation (can be expanded)
        if not self._validate_collected_data(new_config_data):
            return

        if self.config_handler.save_global_config(new_config_data):
            QMessageBox.information(self, _("Save Successful"), _("Global configuration saved."))
            self.config_saved.emit()
            self.accept() # Closes dialog with accept code
        else:
            QMessageBox.critical(self, _("Save Error"), _("Failed to save global configuration. Check logs for details."))

    def _collect_widget_values(self, config_dataclass, prefix: str) -> Dict[str, Any]:
        """
        Recursively collects values from widgets into a dictionary structure.
        """
        collected_data = {}
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            if is_dataclass(field_type):
                collected_data[field_name] = self._collect_widget_values(field_type, full_field_name)
            elif full_field_name in self._widgets:
                widget = self._widgets[full_field_name]
                value = None
                if isinstance(widget, QLineEdit):
                    text = widget.text().strip()
                    if field_type is int:
                        try:
                            value = int(text)
                        except ValueError:
                            value = None # Will be caught by validation
                    elif field_type is float:
                        try:
                            value = float(text)
                        except ValueError:
                            value = None
                    elif field_type == List[str] or field_type == Optional[List[str]]:
                        value = [item.strip() for item in text.split(',') if item.strip()] if text else []
                    elif field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]:
                        import json
                        try:
                            value = json.loads(text) if text else {}
                        except json.JSONDecodeError:
                            value = None
                    else:
                        value = text if text else None
                elif isinstance(widget, QCheckBox):
                    value = widget.isChecked()
                elif isinstance(widget, QSpinBox):
                    value = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    value = widget.value()
                
                # Handle Optional types: if value is None and field is Optional, keep None
                if getattr(field_type, '__origin__', None) is Union and type(None) in getattr(field_type, '__args__', ()):
                    if value is None:
                        collected_data[field_name] = None
                    else:
                        # Try to convert to the actual type if it's not None
                        actual_type = [t for t in field_type.__args__ if t is not type(None)][0]
                        if actual_type == List[str]:
                            collected_data[field_name] = value if isinstance(value, list) else []
                        elif actual_type == Dict[str, str]:
                            collected_data[field_name] = value if isinstance(value, dict) else {}
                        else:
                            collected_data[field_name] = actual_type(value) if value is not None else None
                else:
                    # For non-Optional fields, if value is None, try to use default or raise error
                    if value is None and field_info.default is not fields.MISSING:
                        collected_data[field_name] = field_info.default
                    elif value is None and field_info.default_factory is not fields.MISSING:
                        collected_data[field_name] = field_info.default_factory()
                    else:
                        collected_data[field_name] = value
            else:
                # If widget not found, use default value from schema if available
                if field_info.default is not fields.MISSING:
                    collected_data[field_name] = field_info.default
                elif field_info.default_factory is not fields.MISSING:
                    collected_data[field_name] = field_info.default_factory()
                else:
                    collected_data[field_name] = None # Or raise an error for missing required field

        return collected_data

    def _validate_collected_data(self, data: Dict[str, Any]) -> bool:
        """
        Performs basic validation on the collected data.
        This can be expanded with more specific schema validation.
        """
        # Example: Check if int/float fields were successfully parsed
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    full_field_name = f"Global.{section_name}.{key}"
                    if full_field_name in self._widgets:
                        widget = self._widgets[full_field_name]
                        if isinstance(widget, QLineEdit):
                            field_type = None
                            # Find the actual field type from schema
                            for f_sec in fields(GlobalConfig):
                                if f_sec.name == section_name and is_dataclass(f_sec.type):
                                    for f_item in fields(f_sec.type):
                                        if f_item.name == key:
                                            field_type = f_item.type
                                            break
                                if field_type: break

                            if field_type is int and not isinstance(value, int):
                                QMessageBox.warning(self, _("Validation Error"), _("'{}' in '{}' must be an integer.").format(key, section_name))
                                return False
                            if field_type is float and not isinstance(value, float):
                                QMessageBox.warning(self, _("Validation Error"), _("'{}' in '{}' must be a number.").format(key, section_name))
                                return False
                            if (field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]) and not isinstance(value, dict):
                                QMessageBox.warning(self, _("Validation Error"), _("'{}' in '{}' must be a valid JSON object.").format(key, section_name))
                                return False
        return True
