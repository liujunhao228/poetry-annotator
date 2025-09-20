import logging
import gettext
from dataclasses import fields, is_dataclass, MISSING
from typing import Dict, Any, Optional, List, Union
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton, QMessageBox, QScrollArea, QWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
from ..config_manager import ConfigHandler
from ..help_texts import HELP_TEXTS
from ..help_window import HelpWindow
from ..i18n_config import translate_config_key
from src.config.schema import GlobalModelConfigTemplate

_ = gettext.gettext


def _translate_config_key(k):
    """Translates a configuration key, providing a fallback to a human-readable format."""
    return translate_config_key(k)


class LLMModelConfigDialog(QDialog):
    """
    A dialog panel for editing a specific LLM model's global configuration.
    Dynamically generates UI based on the GlobalModelConfigTemplate schema.
    """
    config_saved = pyqtSignal()

    def __init__(self, model_name: str, config_handler: ConfigHandler, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.config_handler = config_handler
        self.setWindowTitle(_("Edit Model Configuration: {}").format(model_name))
        self.setGeometry(300, 300, 600, 400)

        self._widgets = {}  # To store references to input widgets for dynamic access

        self._setup_ui()
        self._load_config_values()

    def _setup_ui(self):
        """
        Sets up the main layout and dynamically builds the configuration form.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        title_label = QLabel(_("Edit Configuration for Model: {}").format(self.model_name))
        title_label.setProperty("class", "dialog-title")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QFormLayout(self.scroll_content)
        self.form_layout.setLabelAlignment(Qt.AlignRight)
        self.form_layout.setHorizontalSpacing(15)
        self.form_layout.setVerticalSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        self._build_config_form(GlobalModelConfigTemplate, self.form_layout, "Model")

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.help_button = QPushButton(_("Help"))
        self.help_button.clicked.connect(self._show_help)
        button_layout.addStretch()
        button_layout.addWidget(self.help_button)
        self.save_button = QPushButton(_("Save"))
        self.save_button.clicked.connect(self._save_config_values)
        self.cancel_button = QPushButton(_("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
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

            translated_label = _("{}:").format(_translate_config_key(field_name))
            label = QLabel(translated_label)
            widget = self._create_input_widget(field_type, full_field_name)
            if widget:
                tooltip = HELP_TEXTS.get(full_field_name)
                if tooltip:
                    label.setToolTip(tooltip)
                    widget.setToolTip(tooltip)
                parent_layout.addRow(label, widget)
                self._widgets[full_field_name] = widget
            else:
                logging.warning(_("No suitable widget for field '{}' of type {}").format(full_field_name, field_type))

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
        if field_type is str or field_type == Optional[str]:
            return QLineEdit()
        elif field_type is int:
            spin_box = QSpinBox()
            spin_box.setRange(-2147483647, 2147483647)
            return spin_box
        elif field_type is float:
            spin_box = QDoubleSpinBox()
            spin_box.setRange(-3.4028234663852886e+38, 3.4028234663852886e+38) # Max float range
            spin_box.setDecimals(3)
            return spin_box
        elif field_type is bool:
            return QCheckBox()
        elif field_type == List[str] or field_type == Optional[List[str]]:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(_("Comma-separated values"))
            return line_edit
        elif field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(_("JSON string (e.g., {\"key\": \"value\"})"))
            return line_edit
        return None

    def _load_config_values(self):
        """
        Loads current model configuration values into the UI widgets.
        """
        current_config = self.config_handler.get_single_model_config(self.model_name)
        if current_config:
            self._populate_widgets(current_config, "Model")
        else:
            logging.warning(_("No configuration found for model '{}' to load.").format(self.model_name))
            # Clear widgets if no config is available
            for widget in self._widgets.values():
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(False)
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(0)

    def _populate_widgets(self, config_dict: Dict[str, Any], prefix: str):
        """
        Populates widgets with values from a config dictionary.
        """
        for field_info in fields(GlobalModelConfigTemplate):
            field_name = field_info.name
            full_field_name = f"{prefix}.{field_name}"
            value = config_dict.get(field_name)

            if full_field_name in self._widgets:
                widget = self._widgets[full_field_name]
                if isinstance(widget, QLineEdit):
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
        new_config_data = self._collect_widget_values(GlobalModelConfigTemplate, "Model")
        
        if not self._validate_collected_data(new_config_data):
            return

        if self.config_handler.save_single_model_config(self.model_name, new_config_data):
            QMessageBox.information(self, _("Save Successful"), _("Model configuration saved."))
            self.config_saved.emit()
            self.accept()
        else:
            QMessageBox.critical(self, _("Save Error"), _("Failed to save model configuration. Check logs for details."))

    def _collect_widget_values(self, config_dataclass, prefix: str) -> Dict[str, Any]:
        """
        Recursively collects values from widgets into a dictionary structure.
        """
        collected_data = {}
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            if full_field_name in self._widgets:
                widget = self._widgets[full_field_name]
                value = None
                if isinstance(widget, QLineEdit):
                    text = widget.text().strip()
                    if field_type is int:
                        try:
                            value = int(text)
                        except ValueError:
                            value = None
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
                
                # Handle Optional types
                if getattr(field_type, '__origin__', None) is Union and type(None) in getattr(field_type, '__args__', ()):
                    if value is None:
                        collected_data[field_name] = None
                    else:
                        actual_type = [t for t in field_type.__args__ if t is not type(None)][0]
                        if actual_type == List[str]:
                            collected_data[field_name] = value if isinstance(value, list) else []
                        elif actual_type == Dict[str, str]:
                            collected_data[field_name] = value if isinstance(value, dict) else {}
                        else:
                            collected_data[field_name] = actual_type(value) if value is not None else None
                else:
                    if value is None and field_info.default is not MISSING:
                        collected_data[field_name] = field_info.default
                    elif value is None and field_info.default_factory is not MISSING:
                        collected_data[field_name] = field_info.default_factory()
                    else:
                        collected_data[field_name] = value
            else:
                if field_info.default is not MISSING:
                    collected_data[field_name] = field_info.default
                elif field_info.default_factory is not MISSING:
                    collected_data[field_name] = field_info.default_factory()
                else:
                    collected_data[field_name] = None

        return collected_data

    def _validate_collected_data(self, data: Dict[str, Any]) -> bool:
        """
        Performs basic validation on the collected data.
        """
        for key, value in data.items():
            full_field_name = f"Model.{key}"
            if full_field_name in self._widgets:
                widget = self._widgets[full_field_name]
                if isinstance(widget, QLineEdit):
                    field_type = None
                    for f_item in fields(GlobalModelConfigTemplate):
                        if f_item.name == key:
                            field_type = f_item.type
                            break

                    if field_type is int and not isinstance(value, int):
                        QMessageBox.warning(self, _("Validation Error"), _("{field_name} must be an integer.").format(field_name=key))
                        return False
                    if field_type is float and not isinstance(value, float):
                        QMessageBox.warning(self, _("Validation Error"), _("{field_name} must be a number.").format(field_name=key))
                        return False
                    if (field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]) and not isinstance(value, dict):
                        QMessageBox.warning(self, _("Validation Error"), _("{field_name} must be a valid JSON object.").format(field_name=key))
                        return False
        return True
