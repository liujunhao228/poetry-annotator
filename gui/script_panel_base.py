# gui/script_panel_base.py
# Defines the ScriptPanelBase class, a base class for all script-specific GUI panels.
# It provides common interfaces and functionalities for script execution and UI setup.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject
from abc import ABC, abstractmethod, ABCMeta
import gettext

# Define a new metaclass that resolves the conflict
class CombinedMeta(type(QWidget), ABCMeta):
    pass

_ = gettext.gettext

class ScriptPanelBase(QWidget, ABC, metaclass=CombinedMeta):
    """
    Base class for all script-specific GUI panels.
    Provides common interfaces and functionalities for script execution and UI setup.
    """
    script_started = pyqtSignal(str)
    script_finished = pyqtSignal(str, bool) # script_name, success
    script_output = pyqtSignal(str)
    script_progress = pyqtSignal(int, str) # percentage, message

    def __init__(self, script_name: str, parent=None):
        super().__init__(parent)
        self.script_name = script_name
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """
        Initializes the base UI components for the panel.
        Subclasses should call this and then add their specific UI elements.
        """
        self.layout = QVBoxLayout(self)
        self.setup_ui() # Abstract method to be implemented by subclasses

    @abstractmethod
    def setup_ui(self):
        """
        Abstract method to be implemented by subclasses to build their specific UI.
        """
        pass

    @abstractmethod
    def run_script(self):
        """
        Abstract method to be implemented by subclasses to trigger script execution.
        This method should collect parameters and start a ScriptWorker.
        """
        pass

    def _create_worker(self, script_target, params: dict):
        """
        Creates and starts a ScriptWorker in a separate thread.
        Connects worker signals to panel slots.
        """
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, _("Script Running"), _("A script is already running. Please wait for it to finish."))
            return

        from .workers import ScriptWorker # Deferred import to avoid circular dependency
        self.worker = ScriptWorker(script_target, params)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.output_emitted.connect(self._on_worker_output)
        self.worker.progress_updated.connect(self._on_worker_progress)

        self.script_started.emit(self.script_name)
        self.worker.start()

    def _on_worker_finished(self):
        """Slot to handle worker finished signal."""
        self.script_finished.emit(self.script_name, True)
        QMessageBox.information(self, _("Script Finished"), _("{} executed successfully.").format(self.script_name))

    def _on_worker_error(self, error_message: str):
        """Slot to handle worker error signal."""
        self.script_finished.emit(self.script_name, False)
        QMessageBox.critical(self, _("Script Error"), _("{} failed: {}").format(self.script_name, error_message))

    def _on_worker_output(self, output: str):
        """Slot to handle worker output signal."""
        self.script_output.emit(output)

    def _on_worker_progress(self, percentage: int, message: str):
        """Slot to handle worker progress signal."""
        self.script_progress.emit(percentage, message)

    def select_file(self, caption=None, filter="All Files (*.*)"):
        """Provides a common file selection dialog."""
        if caption is None:
            caption = _("Select File")
        file_path, _ = QFileDialog.getOpenFileName(self, caption, "", filter)
        return file_path

    def select_directory(self, caption=None):
        """Provides a common directory selection dialog."""
        if caption is None:
            caption = _("Select Directory")
        dir_path = QFileDialog.getExistingDirectory(self, caption)
        return dir_path

    def show_message(self, title: str, message: str, icon=QMessageBox.Information):
        """Displays a generic message box."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def validate_input(self, inputs: dict) -> bool:
        """
        Placeholder for input validation logic.
        Subclasses should override this for specific validation.
        Returns True if inputs are valid, False otherwise.
        """
        return True
