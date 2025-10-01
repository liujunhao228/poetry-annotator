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
from gui.script_panels.annotation_viewer_panel import AnnotationViewerPanel # New import
from gui.i18n import _
from src.plugin_system.global_manager import get_plugin_manager # New import
from src.plugin_system.loader import PluginLoader # 新增导入
from src.plugin_system.project_config_manager import ProjectPluginConfigManager # 新增导入
import logging # 导入logging

logger = logging.getLogger(__name__)

from src.data.models import set_plugin_manager # 新增导入
from src.data.model_plugin_loader import model_plugin_manager as data_model_plugin_manager # 新增导入

def initialize_plugins():
    """
    Initializes the plugin system by loading plugins from the configuration.
    """
    plugin_manager = get_plugin_manager()
    set_plugin_manager(plugin_manager) # 设置全局插件管理器
    config_file_path = os.path.join(os.path.dirname(__file__), '..', 'project', 'plugins.ini')
    project_root = os.path.dirname(os.path.dirname(__file__)) # 获取项目根目录
    
    try:
        config_manager = ProjectPluginConfigManager(config_file_path)
        PluginLoader.load_plugins_from_config(config_manager, plugin_manager, project_root)
        # 注册数据模型定义插件到全局插件管理器
        from src.data.model_definition_plugin import DataModelDefinitionPlugin
        data_model_plugin = DataModelDefinitionPlugin()
        plugin_manager.register_plugin(data_model_plugin)
        logger.info(_("Plugins initialized and loaded."))
    except Exception as e:
        logger.error(f"Error initializing plugins: {e}")
        # 可以在这里选择退出应用或以降级模式运行
        # sys.exit(1) # 如果插件加载是关键的，可以选择退出

def main():
    """
    Main application entry point.
    Creates the QApplication, MainWindow, and starts the event loop.
    """
    app = QApplication(sys.argv)

    initialize_plugins() # 在创建MainWindow之前加载插件

    main_window = MainWindow()

    # Get the global plugin manager
    plugin_manager = get_plugin_manager()

    # Add script panels
    main_window.add_script_panel(AnnotationStatisticsPanel(), _("Annotation Statistics"))
    main_window.add_script_panel(DistributeTasksPanel(), _("Distribute Tasks"))
    main_window.add_script_panel(ExportPoemAnnotationsPanel(), _("Export Poem Annotations"))
    main_window.add_script_panel(FindDuplicatePoemsPanel(), _("Find Duplicate Poems"))
    main_window.add_script_panel(ProofreadAnnotationsPanel(), _("Proofread Annotations"))
    main_window.add_script_panel(RandomSamplePanel(), _("Random Sample"))
    main_window.add_script_panel(AnnotationViewerPanel(plugin_manager), _("Annotation Viewer")) # New panel

    # After all panels are added, trigger the initial configuration update
    main_window._update_panels_with_project_config()

    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
