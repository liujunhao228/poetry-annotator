# gui/config_panels/llm_config_panel.py
# Panel for managing LLM model configurations.

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QListWidget,
    QFormLayout, QLineEdit, QWidget, QLabel, QListWidgetItem
)
from ..i18n import _
from ..config_manager import ConfigHandler

class LLMConfigPanel(QDialog):
    """
    A dialog for managing LLM model configurations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("LLM Model Configuration"))
        self.setGeometry(200, 200, 800, 600)
        self.config_handler = ConfigHandler()
        self.models = self.config_handler.get_llm_models()
        self._setup_ui()
        self._load_models()

    def _setup_ui(self):
        """
        Sets up the UI components of the dialog.
        """
        top_level_layout = QVBoxLayout(self)

        # Main content area (list and form)
        main_content_layout = QHBoxLayout()

        # Left side: List of models
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.model_list = QListWidget()
        self.model_list.currentItemChanged.connect(self._on_model_selected)
        left_layout.addWidget(self.model_list)

        add_remove_button_layout = QHBoxLayout()
        add_button = QPushButton(_("Add Model"))
        add_button.clicked.connect(self._add_model)
        remove_button = QPushButton(_("Remove Model"))
        remove_button.clicked.connect(self._remove_model)
        add_remove_button_layout.addWidget(add_button)
        add_remove_button_layout.addWidget(remove_button)
        left_layout.addLayout(add_remove_button_layout)

        # Right side: Form for editing model details
        right_widget = QWidget()
        self.form_layout = QFormLayout(right_widget)
        self.model_name_edit = QLineEdit()
        self.api_key_edit = QLineEdit()
        self.base_url_edit = QLineEdit()
        self.form_layout.addRow(_("Model Name:"), self.model_name_edit)
        self.form_layout.addRow(_("API Key:"), self.api_key_edit)
        self.form_layout.addRow(_("Base URL:"), self.base_url_edit)

        main_content_layout.addWidget(left_widget, 1)
        main_content_layout.addWidget(right_widget, 2)

        # Save and Close buttons
        dialog_button_layout = QHBoxLayout()
        dialog_button_layout.addStretch() # Add a spacer to push buttons to the right
        self.save_button = QPushButton(_("Save"))
        self.save_button.clicked.connect(self.save_config)
        self.close_button = QPushButton(_("Close"))
        self.close_button.clicked.connect(self.accept)
        dialog_button_layout.addWidget(self.save_button)
        dialog_button_layout.addWidget(self.close_button)
        
        # Add the main content and button layouts to the top-level layout
        top_level_layout.addLayout(main_content_layout)
        top_level_layout.addLayout(dialog_button_layout)

    def _load_models(self):
        """
        Loads the models into the list widget.
        """
        self.model_list.clear()
        for model_name, model_config in self.models.items():
            item = QListWidgetItem(model_name)
            self.model_list.addItem(item)

    def _on_model_selected(self, current, previous):
        """
        Handles the selection of a model in the list.
        """
        if current:
            model_name = current.text()
            model_config = self.models.get(model_name, {})
            self.model_name_edit.setText(model_name)
            self.api_key_edit.setText(model_config.get("api_key", ""))
            self.base_url_edit.setText(model_config.get("base_url", ""))

    def _add_model(self):
        """
        Adds a new model to the list.
        """
        new_model_name = "new_model"
        i = 1
        while new_model_name in self.models:
            new_model_name = f"new_model_{i}"
            i += 1
        
        self.models[new_model_name] = {"api_key": "", "base_url": ""}
        self._load_models()
        # Select the new model
        items = self.model_list.findItems(new_model_name, Qt.MatchExactly)
        if items:
            self.model_list.setCurrentItem(items[0])

    def _remove_model(self):
        """
        Removes the selected model from the list.
        """
        current_item = self.model_list.currentItem()
        if current_item:
            model_name = current_item.text()
            reply = QMessageBox.question(
                self, _("Remove Model"),
                _("Are you sure you want to remove the model '{}'?").format(model_name),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.models[model_name]
                self._load_models()
                self._clear_form()

    def _clear_form(self):
        """
        Clears the model editing form.
        """
        self.model_name_edit.clear()
        self.api_key_edit.clear()
        self.base_url_edit.clear()

    def save_config(self):
        """
        Saves the LLM configurations.
        """
        # Update the current model's data before saving
        current_item = self.model_list.currentItem()
        if current_item:
            old_model_name = current_item.text()
            new_model_name = self.model_name_edit.text()
            if old_model_name != new_model_name:
                del self.models[old_model_name]
            
            self.models[new_model_name] = {
                "api_key": self.api_key_edit.text(),
                "base_url": self.base_url_edit.text()
            }
        
        # Convert all model data to strings before saving
        models_to_save = {}
        for model_name, model_config in self.models.items():
            models_to_save[model_name] = {k: str(v) for k, v in model_config.items()}

        if self.config_handler.save_llm_models(models_to_save):
            QMessageBox.information(self, _("Save Configuration"), _("Configuration saved successfully!"))
            self.accept()
        else:
            QMessageBox.critical(self, _("Error"), _("Failed to save configuration."))
