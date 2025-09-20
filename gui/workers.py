# gui/workers.py
# Defines the ScriptWorker class, inheriting from QThread.
# This class will run scripts in a separate thread to keep the GUI responsive.

from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os
import logging
import io
from typing import Callable, Any, Dict

# Custom handler to capture logs
class QtSignalHandler(logging.Handler):
    def __init__(self, signal_emitter):
        super().__init__()
        self.signal_emitter = signal_emitter
        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        self.signal_emitter.emit(msg)

class ScriptWorker(QThread):
    """
    A QThread subclass to run external scripts in a separate thread, keeping the GUI responsive.
    Emits signals for script progress, output, errors, and completion.
    """
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    output_emitted = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str) # percentage, message

    def __init__(self, script_name: str, params: dict, parent=None):
        super().__init__(parent)
        self.script_name = script_name
        self.params = params
        self._is_running = True

    def run(self):
        """
        The main execution method for the thread.
        Calls the target script using subprocess and captures its output.
        """
        try:
            script_path = os.path.join("scripts", self.script_name)
            
            args = [sys.executable, script_path]
            for key, value in self.params.items():
                if isinstance(value, bool):
                    if value:
                        args.append(f"--{key}")
                else:
                    if isinstance(value, list):
                        for item in value:
                            args.append(f"--{key}")
                            args.append(str(item))
                    else:
                        args.append(f"--{key}")
                        args.append(str(value))

            self.output_emitted.emit(f"Executing command: {' '.join(args)}\n")

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            while self._is_running:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_emitted.emit(output.strip())

            remaining_output, remaining_error = process.communicate()
            if remaining_output:
                self.output_emitted.emit(remaining_output.strip())
            if remaining_error:
                self.output_emitted.emit(remaining_error.strip())

            if process.returncode != 0:
                error_message = f"Script '{self.script_name}' exited with error code {process.returncode}."
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
            self.wait()

class FunctionWorker(QThread):
    """
    A QThread subclass to run a Python function in a separate thread, keeping the GUI responsive.
    Captures log output and emits it via signals.
    """
    finished = pyqtSignal(object) # Emits the return value of the function
    error_occurred = pyqtSignal(str)
    output_emitted = pyqtSignal(str) # For log messages
    progress_updated = pyqtSignal(int, str) # percentage, message (not directly used by run_distribution_task, but kept for consistency)

    def __init__(self, target_function: Callable, function_args: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.target_function = target_function
        self.function_args = function_args
        self._is_running = True

    def run(self):
        """
        The main execution method for the thread.
        Calls the target function and captures its log output.
        """
        # Create a custom logger for this thread to capture its output
        worker_logger = logging.getLogger(f"FunctionWorker-{self.currentThreadId()}")
        worker_logger.setLevel(logging.DEBUG) # Capture all levels

        # Remove existing handlers to avoid duplicate output
        for handler in worker_logger.handlers[:]:
            worker_logger.removeHandler(handler)

        # Add a custom handler to emit logs as signals
        handler = QtSignalHandler(self.output_emitted)
        worker_logger.addHandler(handler)

        # Temporarily redirect root logger to capture all logs
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        root_logger.handlers = [] # Clear existing handlers
        root_logger.addHandler(handler) # Add our custom handler
        root_logger.setLevel(logging.INFO) # Ensure INFO and above are captured

        try:
            self.output_emitted.emit(f"Executing function: {self.target_function.__name__} with args: {self.function_args}\n")
            
            # Call the target function with its arguments
            result = self.target_function(**self.function_args)
            self.finished.emit(result)

        except Exception as e:
            error_message = f"Function '{self.target_function.__name__}' failed: {e}"
            worker_logger.exception(error_message) # Log the exception with traceback
            self.error_occurred.emit(error_message)
        finally:
            # Restore original root logger handlers
            root_logger.handlers = original_handlers
            root_logger.setLevel(logging.NOTSET) # Reset level
            # Remove the custom handler from worker_logger
            worker_logger.removeHandler(handler)
            handler.close()

    def stop(self):
        """
        Stops the worker thread gracefully.
        For function workers, this primarily means setting a flag.
        The function itself needs to be designed to check this flag if it's long-running.
        """
        self._is_running = False
        # For functions, there's no direct way to "kill" them safely.
        # The function itself would need to check self._is_running if it supports interruption.
        if self.isRunning():
            self.wait()
