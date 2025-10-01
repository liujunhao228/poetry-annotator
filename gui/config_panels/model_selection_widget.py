# gui/config_panels/model_selection_widget.py
# Implements a reusable widget for selecting and managing LLM models within project configurations.

import logging
import gettext
from dataclasses import fields, MISSING
from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QGroupBox, QPushButton, QMessageBox, QInputDialog
)
from PyQt5.QtCore import pyqtSignal, Qt
from ..config_manager import ConfigHandler
from .llm_model_config_dialog import LLMModelConfigDialog
from src.config.schema import GlobalModelConfigTemplate, ProjectModelConfig

_ = gettext.gettext

class ModelSelectionWidget(QWidget):
    """
    A reusable widget for selecting and managing LLM models within project configurations.
    It provides a "transfer list" (穿梭框) pattern for moving models between
    available global models and the project's active models.
    """
    # Signal emitted when the list of project models changes (e.g., for saving)
    project_models_changed = pyqtSignal(list)

    def __init__(self, config_handler: ConfigHandler, parent=None):
        super().__init__(parent)
        self.config_handler = config_handler
        self._setup_ui()
        self._refresh_model_lists() # Initial population

    def _setup_ui(self):
        """
        Sets up the UI for the model selection widget.
        """
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setSpacing(15)

        # Left side: Available Models
        available_models_group_box = QGroupBox(_("Available Models"))
        available_models_layout = QVBoxLayout(available_models_group_box)
        self.available_models_list = QListWidget()
        self.available_models_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.available_models_list.itemDoubleClicked.connect(lambda item: self._edit_model_config(item.text()))
        available_models_layout.addWidget(self.available_models_list)
        
        # Create New Model and Remove Global Model buttons
        create_remove_h_layout = QHBoxLayout()
        create_remove_h_layout.addStretch()
        self.create_new_model_button = QPushButton(_("Create New Model Configuration"))
        self.create_new_model_button.clicked.connect(self._create_new_model_config)
        create_remove_h_layout.addWidget(self.create_new_model_button)
        
        self.remove_global_model_button = QPushButton(_("Remove Selected Global Model"))
        self.remove_global_model_button.clicked.connect(self._remove_global_model_config)
        create_remove_h_layout.addWidget(self.remove_global_model_button)
        create_remove_h_layout.addStretch()
        available_models_layout.addLayout(create_remove_h_layout)

        main_h_layout.addWidget(available_models_group_box)

        # Middle: Transfer Buttons
        transfer_buttons_layout = QVBoxLayout()
        transfer_buttons_layout.addStretch()
        self.add_selected_button = QPushButton(" > ")
        self.add_selected_button.clicked.connect(self._add_selected_models_to_project)
        transfer_buttons_layout.addWidget(self.add_selected_button)

        self.remove_selected_button = QPushButton(" < ")
        self.remove_selected_button.clicked.connect(self._remove_selected_models_from_project)
        transfer_buttons_layout.addWidget(self.remove_selected_button)

        self.add_all_button = QPushButton(" >> ")
        self.add_all_button.clicked.connect(self._add_all_models_to_project)
        transfer_buttons_layout.addWidget(self.add_all_button)

        self.remove_all_button = QPushButton(" << ")
        self.remove_all_button.clicked.connect(self._remove_all_models_from_project)
        transfer_buttons_layout.addWidget(self.remove_all_button)
        transfer_buttons_layout.addStretch()
        main_h_layout.addLayout(transfer_buttons_layout)

        # Right side: Project's Active Models
        active_models_group_box = QGroupBox(_("Project's Active Models"))
        active_models_layout = QVBoxLayout(active_models_group_box)
        self.project_models_list = QListWidget()
        self.project_models_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.project_models_list.itemDoubleClicked.connect(lambda item: self._edit_model_config(item.text()))
        active_models_layout.addWidget(self.project_models_list)
        main_h_layout.addWidget(active_models_group_box)

    def _create_new_model_config(self):
        """
        Prompts the user for a new model name and opens the LLMModelConfigDialog for it.
        """
        model_name, ok = QInputDialog.getText(self, _("Create New Model"), _("Enter a name for the new model:"))
        if ok and model_name:
            model_name = model_name.strip()
            if not model_name:
                QMessageBox.warning(self, _("Invalid Name"), _("Model name cannot be empty."))
                return

            if model_name in self.config_handler.list_all_model_names():
                QMessageBox.warning(self, _("Duplicate Name"), _("A model with the name '{}' already exists. Please choose a different name.").format(model_name))
                return
            
            default_config = {field.name: field.default for field in fields(GlobalModelConfigTemplate) if field.default is not MISSING}
            if 'provider' not in default_config: default_config['provider'] = ""
            if 'model_name' not in default_config: default_config['model_name'] = model_name

            if self.config_handler.save_single_model_config(model_name, default_config):
                QMessageBox.information(self, _("Model Created"), _("New model configuration '{}' created. You can now edit its settings.").format(model_name))
                self._refresh_model_lists()
                self._edit_model_config(model_name)
            else:
                QMessageBox.critical(self, _("Error"), _("Failed to create new model configuration."))

    def _remove_global_model_config(self):
        """
        Removes the selected global model configuration.
        """
        selected_items = self.available_models_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, _("No Model Selected"), _("Please select one or more models to remove."))
            return

        model_names_to_remove = [item.text() for item in selected_items]
        
        reply = QMessageBox.question(
            self, _("Remove Models"),
            _("Are you sure you want to remove the selected global model(s)?\n\n{}").format("\n".join(model_names_to_remove)),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            fail_count = 0
            for model_name in model_names_to_remove:
                if self.config_handler.delete_single_model_config(model_name):
                    success_count += 1
                    # Also remove from project_models_list if it's there
                    for i in range(self.project_models_list.count()):
                        item = self.project_models_list.item(i)
                        if item.text() == model_name:
                            self.project_models_list.takeItem(i)
                            break
                else:
                    fail_count += 1
            
            if success_count > 0:
                QMessageBox.information(self, _("Models Removed"), _("{} model(s) removed successfully.").format(success_count))
            if fail_count > 0:
                QMessageBox.critical(self, _("Error"), _("{} model(s) failed to remove. Check logs for details.").format(fail_count))
            
            self._refresh_model_lists()

    def _add_selected_models_to_project(self):
        """
        Adds selected models from the available models list to the project's active models list.
        """
        selected_items = self.available_models_list.selectedItems()
        for item in selected_items:
            model_name = item.text()
            if not self._is_model_in_list(self.project_models_list, model_name):
                self._add_model_item_to_list(self.project_models_list, model_name)
        self._emit_project_models_changed()

    def _remove_selected_models_from_project(self):
        """
        Removes selected models from the project's active models list.
        """
        selected_items = self.project_models_list.selectedItems()
        for item in selected_items:
            self.project_models_list.takeItem(self.project_models_list.row(item))
        self._emit_project_models_changed()

    def _add_all_models_to_project(self):
        """
        Adds all models from the available models list to the project's active models list.
        """
        for i in range(self.available_models_list.count()):
            item = self.available_models_list.item(i)
            model_name = item.text()
            if not self._is_model_in_list(self.project_models_list, model_name):
                self._add_model_item_to_list(self.project_models_list, model_name)
        self._emit_project_models_changed()

    def _remove_all_models_from_project(self):
        """
        Removes all models from the project's active models list.
        """
        self.project_models_list.clear()
        self._emit_project_models_changed()

    def _is_model_in_list(self, qlist_widget: QListWidget, model_name: str) -> bool:
        """
        Helper to check if a model name exists in a QListWidget.
        """
        for i in range(qlist_widget.count()):
            item = qlist_widget.item(i)
            if item.text() == model_name:
                return True
        return False

    def _add_model_item_to_list(self, qlist_widget: QListWidget, model_name: str):
        """
        Helper to add a model name to a QListWidget.
        """
        if not self._is_model_in_list(qlist_widget, model_name):
            item = QListWidgetItem(model_name)
            qlist_widget.addItem(item)

    def _edit_model_config(self, model_name: str):
        """
        Opens a dialog to edit the configuration of a specific model.
        """
        dialog = LLMModelConfigDialog(model_name, self.config_handler, self)
        dialog.config_saved.connect(self._refresh_model_lists)
        dialog.exec_()

    def _refresh_model_lists(self):
        """
        Refreshes both available and project model lists, preserving the current UI state of project models.
        """
        project_active_models = self.get_project_model_names()
        self.set_project_model_names(project_active_models) # Re-populate to ensure consistency and sorting

    def _populate_model_lists_internal(self, project_active_models: List[str]):
        """
        Internal method to populate both the available models list and the project's active models list.
        This implements a "copy" rather than "move" behavior. The available list always
        shows all globally defined models.
        """
        all_global_models = set(self.config_handler.list_all_model_names())
        project_active_models_set = set(project_active_models)

        self.available_models_list.clear()
        for model_name in sorted(list(all_global_models)):
            self._add_model_item_to_list(self.available_models_list, model_name)

        self.project_models_list.clear()
        for model_name in sorted(list(project_active_models_set)):
            self._add_model_item_to_list(self.project_models_list, model_name)

    def set_project_model_names(self, model_names: List[str]):
        """
        Sets the list of active models for the project.
        This method should be called by the parent panel to initialize the widget.
        """
        self._populate_model_lists_internal(model_names)

    def get_project_model_names(self) -> List[str]:
        """
        Retrieves the currently selected active models for the project from the UI.
        """
        model_names = []
        for i in range(self.project_models_list.count()):
            item = self.project_models_list.item(i)
            model_names.append(item.text())
        return model_names

    def _emit_project_models_changed(self):
        """Emits the signal when project models list changes."""
        self.project_models_changed.emit(self.get_project_model_names())
