# gui/script_panels/distribute_tasks_panel.py
# Implements the DistributeTasksPanel for the distribute_tasks.py script.

import logging
import gettext
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFormLayout, QSpinBox, QMessageBox
)
from ..script_panel_base import ScriptPanelBase

_ = gettext.gettext

class DistributeTasksPanel(ScriptPanelBase):
    """
    GUI panel for the distribute_tasks.py script.
    Allows users to specify database name, input file, output directory,
    number of tasks, and distribution strategy, then run the script.
    """
    def __init__(self, parent=None):
        super().__init__("distribute_tasks.py", parent)

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

        # Output Directory Path Input with Directory Dialog
        output_dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText(_("Select output directory for tasks"))
        self.output_dir_button = QPushButton(_("Browse..."))
        self.output_dir_button.clicked.connect(self._select_output_directory)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(self.output_dir_button)
        form_layout.addRow(QLabel(_("Output Directory:")), output_dir_layout)

        # Number of Tasks Input
        self.num_tasks_input = QSpinBox()
        self.num_tasks_input.setMinimum(1)
        self.num_tasks_input.setMaximum(1000)
        self.num_tasks_input.setValue(10)
        form_layout.addRow(QLabel(_("Number of Tasks:")), self.num_tasks_input)

        # Run Button
        self.run_button = QPushButton(_("Distribute Tasks"))
        self.run_button.clicked.connect(self.run_script)
        form_layout.addRow(self.run_button)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(QLabel(_("Script Output:")))
        self.layout.addWidget(self.script_output_display)

    def _select_input_file(self):
        """
        Opens a file dialog to select the input file path.
        """
        file_path = self.select_file(caption=_("Select Input File"), filter=_("JSON Files (*.json);;Text Files (*.txt);;All Files (*.*)"))
        if file_path:
            self.input_file_input.setText(file_path)

    def _select_output_directory(self):
        """
        Opens a directory dialog to select the output directory path.
        """
        dir_path = self.select_directory(caption=_("Select Output Directory"))
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def validate_input(self, inputs: dict) -> bool:
        """
        Validates the user inputs before running the script.
        """
        if not inputs.get("db"):
            self.show_message(_("Validation Error"), _("Database Name cannot be empty."), QMessageBox.Warning)
            return False
        if not inputs.get("input_file"):
            self.show_message(_("Validation Error"), _("Input File path cannot be empty."), QMessageBox.Warning)
            return False
        if not inputs.get("output_dir"):
            self.show_message(_("Validation Error"), _("Output Directory path cannot be empty."), QMessageBox.Warning)
            return False
        if inputs.get("num_tasks") is None or inputs.get("num_tasks") <= 0:
            self.show_message(_("Validation Error"), _("Number of tasks must be a positive integer."), QMessageBox.Warning)
            return False
        return True

    def run_script(self):
        """
        Collects parameters from UI, validates them, and starts the ScriptWorker.
        """
        params = {
            "db": self.db_name_input.text().strip(),
            "input_file": self.input_file_input.text().strip(),
            "output_dir": self.output_dir_input.text().strip(),
            "num_tasks": self.num_tasks_input.value()
        }

        if self.validate_input(params):
            logging.info(_("Starting '{}' with parameters: {}").format(self.script_name, params))
            self._create_worker(self.script_name, params)
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
