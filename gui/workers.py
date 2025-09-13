# gui/workers.py
# Defines the ScriptWorker class, inheriting from QThread.
# This class will run scripts in a separate thread to keep the GUI responsive.

from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os

class ScriptWorker(QThread):
    """
    A QThread subclass to run scripts in a separate thread, keeping the GUI responsive.
    Emits signals for script progress, output, errors, and completion.
    """
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    output_emitted = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str) # percentage, message

    def __init__(self, script_target, params: dict, parent=None):
        super().__init__(parent)
        self.script_target = script_target
        self.params = params
        self._is_running = True

    def run(self):
        """
        The main execution method for the thread.
        Calls the target script using subprocess and captures its output.
        """
        try:
            # Construct the command to run the script
            # Assuming script_target is a path to a Python script in the 'scripts' directory
            script_path = os.path.join("scripts", self.script_target)
            
            # Build command arguments from params dictionary
            args = [sys.executable, script_path]
            for key, value in self.params.items():
                # Handle boolean flags, assuming they are passed as --flag if True
                if isinstance(value, bool):
                    if value:
                        args.append(f"--{key}")
                else:
                    args.append(f"--{key}")
                    args.append(str(value))

            self.output_emitted.emit(f"Executing command: {' '.join(args)}\n")

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decode stdout/stderr as text
                bufsize=1, # Line-buffered
                universal_newlines=True # Ensure consistent line endings
            )

            # Read stdout and stderr in real-time
            while self._is_running:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_emitted.emit(output.strip())

            # Read any remaining output
            remaining_output, remaining_error = process.communicate()
            if remaining_output:
                self.output_emitted.emit(remaining_output.strip())
            if remaining_error:
                self.output_emitted.emit(remaining_error.strip())

            if process.returncode != 0:
                error_message = f"Script '{self.script_target}' exited with error code {process.returncode}."
                if remaining_error:
                    error_message += f"\nError output:\n{remaining_error.strip()}"
                self.error_occurred.emit(error_message)
            else:
                self.finished.emit()

        except FileNotFoundError:
            self.error_occurred.emit(f"Error: Script file not found at {script_path}")
        except Exception as e:
            self.error_occurred.emit(f"An unexpected error occurred: {e}")

    def stop(self):
        """
        Stops the worker thread gracefully.
        """
        self._is_running = False
        if self.isRunning():
            self.wait() # Wait for the thread to finish its current operation
