# gui/script_panels/random_sample_panel.py
# Implements the RandomSamplePanel for the random_sample.py script.

import logging
import gettext
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFormLayout, QSpinBox, QMessageBox, QFileDialog, QCheckBox, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt
from ..script_panel_base import ScriptPanelBase
from src.config.manager import get_config_manager
import os

_ = gettext.gettext

class RandomSamplePanel(ScriptPanelBase):
    """
    GUI panel for the random_sample.py script.
    Allows users to specify database name, output directory, sample size, and other options, then run the script.
    """
    def __init__(self, parent=None):
        super().__init__("random_sample.py", parent)

    def setup_ui(self):
        """
        Builds the specific UI for the Random Sample script.
        """
        self.script_output_display = QTextEdit()
        self.script_output_display.setReadOnly(True)
        self.script_output_display.setPlaceholderText(_("Script output will appear here..."))
        # Add a property for styling
        self.script_output_display.setProperty("class", "output-display")

        # Connect signals from base class to update this panel's output display
        self.script_output.connect(self._update_output_display)
        self.script_started.connect(self._on_script_started)
        self.script_finished.connect(self._on_script_finished)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)  # Right-align labels
        form_layout.setHorizontalSpacing(15)  # Add horizontal spacing
        form_layout.setVerticalSpacing(10)  # Add vertical spacing

        # Database Name Input
        self.db_name_input = QLineEdit()
        self.db_name_input.setPlaceholderText(_("Enter database name (e.g., default)"))
        form_layout.addRow(QLabel(_("Database Name:")), self.db_name_input)

        # Sample Size Input
        self.sample_size_input = QSpinBox()
        self.sample_size_input.setMinimum(1)
        self.sample_size_input.setMaximum(10000) # Arbitrary max, can be adjusted
        self.sample_size_input.setValue(100)
        form_layout.addRow(QLabel(_("Sample Size:")), self.sample_size_input)

        # Exclude Annotated Checkbox
        self.exclude_annotated_checkbox = QCheckBox(_("Exclude already annotated poems"))
        self.exclude_annotated_checkbox.stateChanged.connect(self._on_exclude_annotated_changed)
        form_layout.addRow(QLabel(_("Exclude Annotated:")), self.exclude_annotated_checkbox)

        # Model Identifier Input (enabled only when exclude_annotated is checked)
        self.model_identifier_input = QLineEdit()
        self.model_identifier_input.setPlaceholderText(_("Enter model identifier (optional)"))
        self.model_identifier_input.setEnabled(False)
        form_layout.addRow(QLabel(_("Model Identifier:")), self.model_identifier_input)

        # Active Only Checkbox
        self.active_only_checkbox = QCheckBox(_("Only sample active poems"))
        form_layout.addRow(QLabel(_("Active Only:")), self.active_only_checkbox)

        # Sorting Options
        self.sort_group = QButtonGroup(self)
        self.sort_default_radio = QRadioButton(_("Default (random)"))
        self.sort_default_radio.setChecked(True)
        self.sort_asc_radio = QRadioButton(_("Sort ascending"))
        self.sort_no_shuffle_radio = QRadioButton(_("No shuffle"))
        self.sort_group.addButton(self.sort_default_radio)
        self.sort_group.addButton(self.sort_asc_radio)
        self.sort_group.addButton(self.sort_no_shuffle_radio)
        
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(self.sort_default_radio)
        sort_layout.addWidget(self.sort_asc_radio)
        sort_layout.addWidget(self.sort_no_shuffle_radio)
        form_layout.addRow(QLabel(_("Sorting:")), sort_layout)

        # Output Directory Path Input with File Dialog
        output_dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText(_("Select output directory for random sample"))
        self.output_dir_button = QPushButton(_("Browse..."))
        self.output_dir_button.clicked.connect(self._select_output_dir)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(self.output_dir_button)
        form_layout.addRow(QLabel(_("Output Directory:")), output_dir_layout)

        # Number of Files Input
        self.num_files_input = QSpinBox()
        self.num_files_input.setMinimum(1)
        self.num_files_input.setMaximum(100) # Arbitrary max
        self.num_files_input.setValue(1)
        form_layout.addRow(QLabel(_("Number of Files:")), self.num_files_input)

        # Run Button
        self.run_button = QPushButton(_("Generate Random Sample"))
        self.run_button.clicked.connect(self.run_script)
        # Center the button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.run_button)
        button_layout.addStretch()
        form_layout.addRow(button_layout)

        self.layout.addLayout(form_layout)
        # Add a title for the output section
        output_title = QLabel(_("Script Output:"))
        output_title.setProperty("class", "section-title")
        self.layout.addWidget(output_title)
        self.layout.addWidget(self.script_output_display)

    def _select_output_dir(self):
        """
        Opens a directory dialog to select the output directory path.
        """
        dir_path = QFileDialog.getExistingDirectory(self, _("Select Output Directory"))
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def _on_exclude_annotated_changed(self, state):
        """
        Enables/disables the model identifier input based on the exclude annotated checkbox state.
        """
        self.model_identifier_input.setEnabled(state == Qt.Checked)

    def validate_input(self, inputs: dict) -> bool:
        """
        Validates the user inputs before running the script.
        """
        if not inputs.get("db"):
            self.show_message(_("Validation Error"), _("Database Name cannot be empty."), QMessageBox.Warning)
            return False
        if not inputs.get("output_dir"):
            self.show_message(_("Validation Error"), _("Output Directory cannot be empty."), QMessageBox.Warning)
            return False
        if inputs.get("sample_size") is None or inputs.get("sample_size") <= 0:
            self.show_message(_("Validation Error"), _("Sample Size must be a positive integer."), QMessageBox.Warning)
            return False
        if inputs.get("num_files") is None or inputs.get("num_files") <= 0:
            self.show_message(_("Validation Error"), _("Number of Files must be a positive integer."), QMessageBox.Warning)
            return False
        return True

    def run_script(self):
        """
        Collects parameters from UI, validates them, and starts the ScriptWorker.
        """
        db_name = self.db_name_input.text().strip()
        output_dir = self.output_dir_input.text().strip()
        
        # Use the db_name to get source_dir from config
        source_dir = self._get_source_dir_from_config(db_name)
        
        if not source_dir:
            self.show_message(_("Configuration Error"), _("Could not determine source directory for database: {}").format(db_name), QMessageBox.Warning)
            return

        params = {
            "source-dir": source_dir,
            "output-dir": output_dir,
            "count": self.sample_size_input.value(),
            "exclude-annotated": self.exclude_annotated_checkbox.isChecked(),
            "active-only": self.active_only_checkbox.isChecked(),
            "num-files": self.num_files_input.value()
        }
        
        # Add model parameter only if exclude annotated is checked and model identifier is provided
        if self.exclude_annotated_checkbox.isChecked() and self.model_identifier_input.text().strip():
            params["model"] = self.model_identifier_input.text().strip()
            
        # Add sort parameters
        if self.sort_asc_radio.isChecked():
            params["sort"] = True
        elif self.sort_no_shuffle_radio.isChecked():
            params["no-shuffle"] = True
        # If sort_default_radio is checked, we don't add any sort parameters (default behavior)

        if self.validate_input({
            "db": db_name,
            "output_dir": output_dir,
            "sample_size": self.sample_size_input.value(),
            "num_files": self.num_files_input.value()
        }):
            logging.info(_("Starting '{}' with parameters: {}").format(self.script_name, params))
            self._create_worker(self.script_name, params)
        else:
            logging.warning(_("Input validation failed for '{}'.").format(self.script_name))

    def _get_source_dir_from_config(self, db_name: str) -> str:
        """
        Gets source directory path from config using database name.
        """
        try:
            config_manager = get_config_manager()
            # Get all available projects to find the matching one
            available_projects = config_manager.get_available_project_configs()
            
            # Look for a project that matches the database name
            matching_project = None
            for project in available_projects:
                project_config_path = f"config/projects/{project}"
                if os.path.exists(project_config_path):
                    # Load the project config to check its output directory
                    import configparser
                    project_config = configparser.ConfigParser()
                    project_config.read(project_config_path, encoding='utf-8')
                    if project_config.has_section('Data'):
                        output_dir = project_config.get('Data', 'output_dir', fallback='')
                        if os.path.basename(output_dir) == db_name:
                            matching_project = project
                            break
            
            # If not found in projects, check the main project config
            if not matching_project:
                main_project_config = config_manager.get_project_config()
                if main_project_config and main_project_config.data_path:
                    if os.path.basename(main_project_config.data_path.output_dir) == db_name:
                        # Use main project config
                        data_config = config_manager.get_effective_data_config()
                        return data_config.get('source_dir')
            
            # If we found a matching project, load its config
            if matching_project:
                project_config_path = f"config/projects/{matching_project}"
                import configparser
                project_config = configparser.ConfigParser()
                project_config.read(project_config_path, encoding='utf-8')
                if project_config.has_section('Data'):
                    source_dir = project_config.get('Data', 'source_dir', fallback='')
                    return source_dir
                    
            # Fallback to default path if we can't find a match
            return f"data/source_json/{db_name}"
        except Exception as e:
            logging.error(f"Error getting source directory for database {db_name}: {e}")
            return None

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
