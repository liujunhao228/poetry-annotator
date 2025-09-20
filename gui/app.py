# gui/app.py
# The main application entry point for the GUI.
# It will create the QApplication and the MainWindow, then start the event loop.

# Workaround for a bug in the Python mimetypes module on Windows
import mimetypes
mimetypes.read_windows_registry = lambda *args, **kwargs: None

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
# from PyQt5.QtCore import QTranslator, QLocale, QCoreApplication # Removed Qt's i18n imports
from gui.main_window import MainWindow
# Import script panels here as they are implemented
from gui.script_panels.annotation_statistics_panel import AnnotationStatisticsPanel
from gui.script_panels.distribute_tasks_panel import DistributeTasksPanel
from gui.script_panels.export_poem_annotations_panel import ExportPoemAnnotationsPanel
from gui.script_panels.find_duplicate_poems_panel import FindDuplicatePoemsPanel
from gui.script_panels.proofread_annotations_panel import ProofreadAnnotationsPanel
from gui.script_panels.random_sample_panel import RandomSamplePanel
from gui.i18n import _

def main():
    """
    Main application entry point.
    Creates the QApplication, MainWindow, and starts the event loop.
    """
    app = QApplication(sys.argv)

    main_window = MainWindow()

    # Add script panels
    main_window.add_script_panel(AnnotationStatisticsPanel(), _("Annotation Statistics"))
    main_window.add_script_panel(DistributeTasksPanel(), _("Distribute Tasks"))
    main_window.add_script_panel(ExportPoemAnnotationsPanel(), _("Export Poem Annotations"))
    main_window.add_script_panel(FindDuplicatePoemsPanel(), _("Find Duplicate Poems"))
    main_window.add_script_panel(ProofreadAnnotationsPanel(), _("Proofread Annotations"))
    main_window.add_script_panel(RandomSamplePanel(), _("Random Sample"))

    # After all panels are added, trigger the initial configuration update
    main_window._update_panels_with_project_config()

    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
