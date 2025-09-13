# gui/help_window.py
# Implements a window to display help information for configuration settings.

import gettext
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
)
from .help_texts import HELP_TEXTS

_ = gettext.gettext

class HelpWindow(QDialog):
    """
    A dialog that displays help information for application settings.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Configuration Help"))
        self.setGeometry(300, 300, 700, 500)
        self._setup_ui()

    def _setup_ui(self):
        """
        Sets up the UI components of the help window.
        """
        main_layout = QVBoxLayout(self)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        main_layout.addWidget(self.text_browser)

        self._populate_help_content()

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.close_button = QPushButton(_("Close"))
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

    def _populate_help_content(self):
        """
        Populates the text browser with formatted help content.
        """
        html_content = f"<h1>{_('Configuration Options')}</h1>"
        html_content += "<dl>"

        for key, description in sorted(HELP_TEXTS.items()):
            # Make the key more readable
            readable_key = key.replace('Global.', '').replace('.', ' &rarr; ').replace('_', ' ').title()
            html_content += f"<dt><b>{readable_key}</b></dt>"
            html_content += f"<dd>{description}</dd><br>"

        html_content += "</dl>"
        self.text_browser.setHtml(html_content)
