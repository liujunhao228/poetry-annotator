# gui/script_panels/distribute_tasks_panel.py
# Implements the DistributeTasksPanel for the distribute_tasks.py script.

import logging
import gettext
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFormLayout, QSpinBox, QMessageBox,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt
from ..script_panel_base import ScriptPanelBase
from src.llm_factory import llm_factory
from src.config.manager import config_manager # Import config_manager
from src.task_distribution.manager import run_distribution_task # Import the new function

_ = gettext.gettext

class DistributeTasksPanel(ScriptPanelBase):
    """
    GUI panel for the distribute_tasks.py script.
    Allows users to specify database name, input file, output directory,
    number of tasks, and distribution strategy, then run the script.
    """
    def __init__(self, parent=None):
        super().__init__("Distribute Tasks", parent) # Changed script_name to a more descriptive title

    def setup_ui(self):
        """
        Builds the specific UI for the Distribute Tasks script.
        """
        self.script_output_display = QTextEdit()
        self.script_output_display.setReadOnly(True)
        self.script_output_display.setPlaceholderText(_("Script output will appear here..."))

        # Connect signals from base class to update this panel's output display
        self.script_output.connect(self._update_output_display)
        self.script_started.connect(self._on_script_started)
        self.script_finished.connect(self._on_script_finished)

        form_layout = QFormLayout()

        # Database Name Input
        self.db_name_input = QLineEdit()
        self.db_name_input.setPlaceholderText(_("Enter database name (e.g., default)"))
        form_layout.addRow(QLabel(_("Database Name:")), self.db_name_input)

        # Input File Path Input with File Dialog
        input_file_layout = QHBoxLayout()
        self.input_file_input = QLineEdit()
        self.input_file_input.setPlaceholderText(_("Select input file (e.g., list of poems)"))
        self.input_file_button = QPushButton(_("Browse..."))
        self.input_file_button.clicked.connect(self._select_input_file)
        input_file_layout.addWidget(self.input_file_input)
        input_file_layout.addWidget(self.input_file_button)
        form_layout.addRow(QLabel(_("Input File:")), input_file_layout)

        # Number of Tasks Input
        self.num_tasks_input = QSpinBox()
        self.num_tasks_input.setMinimum(1)
        self.num_tasks_input.setMaximum(1000)
        self.num_tasks_input.setValue(10)
        form_layout.addRow(QLabel(_("Chunk Size:")), self.num_tasks_input)

        # Model Selection
        model_selection_layout = QVBoxLayout()
        model_selection_layout.addWidget(QLabel(_("Select Models:")))
        
        self.model_list_widget = QListWidget()
        self.model_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self._populate_model_list()
        model_selection_layout.addWidget(self.model_list_widget)

        select_all_button = QPushButton(_("Select All Models"))
        select_all_button.clicked.connect(self._select_all_models)
        model_selection_layout.addWidget(select_all_button)

        form_layout.addRow(model_selection_layout)

        # Run Button
        self.run_button = QPushButton(_("Distribute Tasks"))
        self.run_button.clicked.connect(self.run_script)
        form_layout.addRow(self.run_button)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(QLabel(_("Script Output:")))
        self.layout.addWidget(self.script_output_display)

    def _populate_model_list(self):
        """
        Populates the model list widget with configured LLM models.
        """
        self.model_list_widget.clear()
        try:
            # Get model names from project config
            # Access project_config directly from the config_manager instance
            if config_manager.project_config and hasattr(config_manager.project_config, 'model'):
                project_activated_models = config_manager.project_config.model.model_names
            else:
                project_activated_models = []
                logging.info("Project config or 'Model' section not found in project.ini.")
            
            if project_activated_models:
                # Also get all configured models to ensure selected models are valid
                all_configured_models = llm_factory.list_configured_models().keys()

                for model_name in sorted(project_activated_models):
                    if model_name in all_configured_models:
                        item = QListWidgetItem(model_name)
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Unchecked)
                        self.model_list_widget.addItem(item)
                    else:
                        logging.warning(f"Model '{model_name}' from project.ini is not a configured LLM model.")
            else:
                logging.info("No 'model_names' found in project.ini [Model] section or project config is not loaded.")

        except Exception as e:
            logging.error(f"Failed to load project activated models: {e}")
            self.show_message(_("Error"), _(f"Failed to load project activated models: {e}"), QMessageBox.Critical)

    def _select_all_models(self):
        """
        Selects or deselects all models in the list.
        """
        is_all_checked = all(self.model_list_widget.item(i).checkState() == Qt.Checked for i in range(self.model_list_widget.count()))
        new_state = Qt.Unchecked if is_all_checked else Qt.Checked
        for i in range(self.model_list_widget.count()):
            self.model_list_widget.item(i).setCheckState(new_state)

    def _select_input_file(self):
        """
        Opens a file dialog to select the input file path.
        """
        file_path = self.select_file(caption=_("Select Input File"), filter=_("JSON Files (*.json);;Text Files (*.txt);;All Files (*.*)"))
        if file_path:
            self.input_file_input.setText(file_path)

    def validate_input(self, inputs: dict) -> bool:
        """
        Validates the user inputs before running the script.
        """
        if not inputs.get("db_name"): # Changed from "db" to "db_name"
            self.show_message(_("Validation Error"), _("Database Name cannot be empty."), QMessageBox.Warning)
            return False
        if not inputs.get("id_file") and not inputs.get("id_dir"): # Changed from "id-file" to "id_file"
            self.show_message(_("Validation Error"), _("Input File or Input Directory path cannot be empty."), QMessageBox.Warning)
            return False
        if inputs.get("chunk_size") is None or inputs.get("chunk_size") <= 0: # Changed from "chunk-size" to "chunk_size"
            self.show_message(_("Validation Error"), _("Chunk size must be a positive integer."), QMessageBox.Warning)
            return False
        
        selected_models = inputs.get("selected_models") # Changed from "selected-models" to "selected_models"
        if not selected_models:
            self.show_message(_("Validation Error"), _("Please select at least one model."), QMessageBox.Warning)
            return False
        
        return True

    def _get_selected_models(self) -> list:
        """
        Returns a list of selected model names from the QListWidget.
        """
        selected_models = []
        for i in range(self.model_list_widget.count()):
            item = self.model_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_models.append(item.text())
        return selected_models

    def run_script(self):
        """
        Collects parameters from UI, validates them, and starts the FunctionWorker.
        """
        selected_models = self._get_selected_models()
        
        # Map GUI parameters to function parameters
        function_params = {
            "db_name": self.db_name_input.text().strip(),
            "id_file": self.input_file_input.text().strip(),
            "chunk_size": self.num_tasks_input.value(),
            "selected_models": selected_models,
            "force_rerun": False, # Add default values for other parameters
            "fresh_start": False,
            "dry_run": False,
            "full_dry_run": False
        }

        if self.validate_input(function_params):
            logging.info(_("Starting '{}' with parameters: {}").format(self.script_name, function_params))
            # Use the new _create_function_worker method from ScriptPanelBase
            self._create_function_worker(run_distribution_task, function_params)
        else:
            logging.warning(_("Input validation failed for '{}'.").format(self.script_name))

    def _update_output_display(self, output: str):
        """
        Appends script output to the QTextEdit display.
        """
        self.script_output_display.append(output)

    def _on_script_started(self, script_name: str):
        """
        Handles actions when the script starts.
        """
        self.script_output_display.clear()
        self.script_output_display.append(_("--- {} Started ---").format(script_name))
        self.run_button.setEnabled(False) # Disable button while script is running
        logging.info(_("Script '{}' started.").format(script_name))

    def _on_script_finished(self, script_name: str, success: bool):
        """
        Handles actions when the script finishes.
        """
        status = _("successfully") if success else _("with errors")
        self.script_output_display.append(_("--- {} Finished {} ---").format(script_name, status))
        self.run_button.setEnabled(True) # Re-enable button
        logging.info(_("Script '{}' finished {}.").format(script_name, status))

    def update_database_name(self, db_name: str):
        """
        Updates the database name input field and sets it to read-only.
        """
        if db_name:
            self.db_name_input.setText(db_name)
            self.db_name_input.setReadOnly(True)
