# gui/utils.py
# Provides utility functions and classes for the GUI, such as logging redirection.

import logging
from PyQt5.QtCore import QObject, pyqtSignal

class LogStreamHandler(logging.Handler, QObject):
    """
    A custom logging handler that emits log records as Qt signals.
    This allows redirecting Python's logging output to GUI components.
    """
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        """
        Emit a log record.
        """
        msg = self.format(record)
        self.log_signal.emit(msg)
