# gui/script_panels/random_sample_panel.py
# Implements the RandomSamplePanel for the random_sample.py script.

import logging
import gettext
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFormLayout, QSpinBox, QMessageBox, QFileDialog
)
from ..script_panel_base import ScriptPanelBase

_ = gettext.gettext

class RandomSamplePanel(ScriptPanelBase):
    """
    GUI panel for the random_sample.py script.
    Allows users to specify database name, output file, and sample size, then run the script.
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

        # Connect signals from base class to update this panel's output display
        self.script_output.connect(self._update_output_display)
        self.script_started.connect(self._on_script_started)
        self.script_finished.connect(self._on_script_finished)

        form_layout = QFormLayout()

        # Database Name Input
        self.db_name_input = QLineEdit()
        self.db_name_input.setPlaceholderText(_("Enter database name (e.g., default)"))
        form_layout.addRow(QLabel(_("Database Name:")), self.db_name_input)

        # Output File Path Input with File Dialog
        output_file_layout = QHBoxLayout()
        self.output_file_input = QLineEdit()
        self.output_file_input.setPlaceholderText(_("Select output file path for random sample"))
        self.output_file_button = QPushButton(_("Browse..."))
        self.output_file_button.clicked.connect(self._select_output_file)
        output_file_layout.addWidget(self.output_file_input)
        output_file_layout.addWidget(self.output_file_button)
        form_layout.addRow(QLabel(_("Output File:")), output_file_layout)

        # Sample Size Input
        self.sample_size_input = QSpinBox()
        self.sample_size_input.setMinimum(1)
        self.sample_size_input.setMaximum(10000) # Arbitrary max, can be adjusted
        self.sample_size_input.setValue(100)
        form_layout.addRow(QLabel(_("Sample Size:")), self.sample_size_input)

        # Run Button
        self.run_button = QPushButton(_("Generate Random Sample"))
        self.run_button.clicked.connect(self.run_script)
        form_layout.addRow(self.run_button)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(QLabel(_("Script Output:")))
        self.layout.addWidget(self.script_output_display)

    def _select_output_file(self):
        """
        Opens a file dialog to select the output file path.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, _("Select Output File"), "", _("JSON Files (*.json);;Text Files (*.txt);;All Files (*.*)"))
        if file_path:
            self.output_file_input.setText(file_path)

    def validate_input(self, inputs: dict) -> bool:
        """
        Validates the user inputs before running the script.
        """
        if not inputs.get("db"):
            self.show_message(_("Validation Error"), _("Database Name cannot be empty."), QMessageBox.Warning)
            return False
        if not inputs.get("output"):
            self.show_message(_("Validation Error"), _("Output File path cannot be empty."), QMessageBox.Warning)
            return False
        if inputs.get("sample_size") is None or inputs.get("sample_size") <= 0:
            self.show_message(_("Validation Error"), _("Sample Size must be a positive integer."), QMessageBox.Warning)
            return False
        return True

    def run_script(self):
        """
        Collects parameters from UI, validates them, and starts the ScriptWorker.
        """
        params = {
            "db": self.db_name_input.text().strip(),
            "output": self.output_file_input.text().strip(),
            "sample_size": self.sample_size_input.value()
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
