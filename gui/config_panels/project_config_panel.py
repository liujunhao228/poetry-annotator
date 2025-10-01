# gui/config_panels/project_config_panel.py
# Implements the ProjectConfigPanel for editing project-specific configurations.

import logging
import sys
import gettext
from dataclasses import fields, is_dataclass, MISSING
from typing import Dict, Any, Optional, List, Union
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton, QFileDialog, QMessageBox,
    QComboBox, QScrollArea, QWidget, QGroupBox, QInputDialog,
    QTabWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
from ..config_manager import ConfigHandler
from ..help_texts import HELP_TEXTS
from ..help_window import HelpWindow
from ..i18n_config import translate_config_key
from src.config.schema import ProjectConfig, ProjectLLMConfig, ProjectDatabaseConfig, \
    ProjectDataPathConfig, ProjectPromptConfig, ProjectLoggingConfig, \
    ProjectVisualizerConfig, ProjectModelConfig, ProjectPluginsConfig, PluginConfig
from .llm_model_config_dialog import LLMModelConfigDialog # Import the new dialog
from .model_selection_widget import ModelSelectionWidget # Import the new widget
from .plugin_selection_widget import PluginSelectionWidget # Import the new widget

_ = gettext.gettext


def _translate_config_key(k):
    """Translates a configuration key, providing a fallback to a human-readable format."""
    return translate_config_key(k)


class ProjectConfigPanel(QDialog):
    """
    A dialog panel for editing project-specific configurations.
    Dynamically generates UI based on the ProjectConfig schema.
    Includes functionality to switch between available projects.
    """
    config_saved = pyqtSignal()
    project_switched = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Edit Project Configuration"))
        self.setGeometry(200, 200, 800, 600)

        self.config_handler = ConfigHandler()
        self._widgets = {} # To store references to input widgets for dynamic access
        # self._plugin_checkboxes = {} # Removed, now managed by PluginSelectionWidget
        self.current_project_name = self.config_handler.get_active_project()

        self._setup_ui()
        self._load_config_values()

    def _setup_ui(self):
        """
        Sets up the main layout and dynamically builds the configuration form.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)  # Add spacing between elements

        # Add a title for the dialog
        title_label = QLabel(_("Edit Project Configuration"))
        title_label.setProperty("class", "dialog-title")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Project Selection
        project_selection_layout = QHBoxLayout()
        project_selection_layout.setSpacing(10)  # Add spacing between elements
        project_selection_layout.addWidget(QLabel(_("Active Project:")))
        self.project_combo = QComboBox()
        self.project_combo.addItems(self.config_handler.get_available_projects())
        self.project_combo.setCurrentText(self.current_project_name)
        self.project_combo.currentTextChanged.connect(self._on_project_selected)
        project_selection_layout.addWidget(self.project_combo)
        main_layout.addLayout(project_selection_layout)

        # 使用 QTabWidget 来组织配置项
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)  # 将标签页放在顶部
        main_layout.addWidget(self.tab_widget)

        # 为每个一级嵌套数据类创建一个选项卡
        self._build_config_tabs(ProjectConfig, "Project")

    def _build_config_tabs(self, config_dataclass, prefix: str):
        """
        为每个一级嵌套数据类创建一个选项卡，并在每个选项卡中构建相应的配置表单。
        跳过没有字段的数据类（如ProjectLLMConfig, ProjectLoggingConfig, ProjectVisualizerConfig）。
        """
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            # 只处理一级嵌套的数据类，并跳过没有字段的数据类
            if is_dataclass(field_type) and field_type not in [ProjectPluginsConfig, ProjectModelConfig]:
                # 检查数据类是否有字段
                try:
                    field_list = fields(field_type)
                    if len(field_list) == 0:
                        # 跳过没有字段的数据类
                        continue
                except TypeError:
                    # 如果不是数据类，则继续处理
                    pass

                # 创建一个新的 QWidget 作为选项卡的内容
                tab_content = QWidget()
                tab_layout = QVBoxLayout(tab_content)
                tab_layout.setSpacing(10)  # Add spacing between elements

                # 创建一个滚动区域，以防内容过多
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_content = QWidget()
                form_layout = QFormLayout(scroll_content)
                form_layout.setLabelAlignment(Qt.AlignRight)  # Right-align labels
                form_layout.setHorizontalSpacing(15)  # Add horizontal spacing
                form_layout.setVerticalSpacing(10)  # Add vertical spacing
                scroll_area.setWidget(scroll_content)
                tab_layout.addWidget(scroll_area)

                # 在滚动区域的内容中构建表单
                self._build_config_form(field_type, form_layout, full_field_name)

                # 将选项卡添加到 QTabWidget
                translated_tab_name = _translate_config_key(field_name)
                self.tab_widget.addTab(tab_content, translated_tab_name)

            # 特殊处理插件和模型配置
            elif field_type is ProjectPluginsConfig:
                # 创建一个新的 QWidget 作为选项卡的内容
                tab_content = QWidget()
                tab_layout = QVBoxLayout(tab_content)
                tab_layout.setSpacing(10)  # Add spacing between elements

                # 创建一个滚动区域，以防内容过多
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_content = QWidget()
                form_layout = QFormLayout(scroll_content)
                form_layout.setLabelAlignment(Qt.AlignRight)  # Right-align labels
                form_layout.setHorizontalSpacing(15)  # Add horizontal spacing
                form_layout.setVerticalSpacing(10)  # Add vertical spacing
                scroll_area.setWidget(scroll_content)
                tab_layout.addWidget(scroll_area)

                # 实例化 PluginSelectionWidget 并添加到选项卡布局
                self.plugin_selection_widget = PluginSelectionWidget(self.config_handler, self)
                self.plugin_selection_widget.plugins_changed.connect(self._on_plugins_changed)
                tab_layout.addWidget(self.plugin_selection_widget)

                # 将选项卡添加到 QTabWidget
                translated_tab_name = _translate_config_key(field_name)
                self.tab_widget.addTab(tab_content, translated_tab_name)

            elif field_type is ProjectModelConfig:
                # 创建一个新的 QWidget 作为选项卡的内容
                tab_content = QWidget()
                tab_layout = QVBoxLayout(tab_content)
                tab_layout.setSpacing(10)  # Add spacing between elements

                # 实例化 ModelSelectionWidget 并添加到选项卡布局
                self.model_selection_widget = ModelSelectionWidget(self.config_handler, self)
                self.model_selection_widget.project_models_changed.connect(self._on_project_models_changed)
                tab_layout.addWidget(self.model_selection_widget)

                # 将选项卡添加到 QTabWidget
                translated_tab_name = _translate_config_key(field_name)
                self.tab_widget.addTab(tab_content, translated_tab_name)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons
        self.help_button = QPushButton(_("Help"))
        self.help_button.clicked.connect(self._show_help)
        button_layout.addStretch()
        button_layout.addWidget(self.help_button)
        self.save_button = QPushButton(_("Save"))
        self.save_button.clicked.connect(self._save_config_values)
        self.cancel_button = QPushButton(_("Cancel"))
        self.cancel_button.clicked.connect(self.reject)  # Closes dialog with reject code
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        # 将按钮布局添加到主布局中，而不是 tab_layout
        self.layout().addLayout(button_layout)

    def _on_plugins_changed(self, plugin_states: Dict[str, bool]):
        """
        Slot to handle changes in the PluginSelectionWidget's plugin states.
        For now, it just logs the change.
        """
        logging.debug(_("Project plugins changed: {}").format(plugin_states))

    def _on_project_models_changed(self, model_names: List[str]):
        """
        Slot to handle changes in the ModelSelectionWidget's project models list.
        This can be used to update other parts of the UI or trigger saves if needed.
        For now, it just logs the change.
        """
        logging.debug(_("Project models changed: {}").format(model_names))

    def _build_config_form(self, config_dataclass, parent_layout: QFormLayout, prefix: str):
        """
        Recursively builds the form layout for a given dataclass.
        """
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            if field_type is ProjectPluginsConfig:
                # Plugin selection is now handled by PluginSelectionWidget in _build_config_tabs
                # No need to build it here recursively.
                pass
            elif field_type is ProjectModelConfig:
                # Model selection is now handled by ModelSelectionWidget in _build_config_tabs
                # No need to build it here recursively.
                pass
            elif is_dataclass(field_type):
                # Create a group for nested dataclasses
                group_layout = QFormLayout()
                group_label = QLabel(_("<b>{} Settings</b>").format(_translate_config_key(field_name)))
                parent_layout.addRow(group_label)
                parent_layout.addRow(group_layout)
                self._build_config_form(field_type, group_layout, full_field_name)
            else:
                translated_label = _("{}:").format(_translate_config_key(field_name))
                label = QLabel(translated_label)
                widget = self._create_input_widget(field_type, full_field_name)
                if widget:
                    tooltip = HELP_TEXTS.get(full_field_name)
                    if tooltip:
                        label.setToolTip(tooltip)
                        widget.setToolTip(tooltip)
                    parent_layout.addRow(label, widget)
                    self._widgets[full_field_name] = widget
                else:
                    logging.warning(_("No suitable widget for field '{}' of type {}").format(full_field_name, field_type))

    def _show_help(self):
        """
        Displays the centralized help window.
        """
        help_dialog = HelpWindow(self)
        help_dialog.exec_()

    def _create_input_widget(self, field_type, full_field_name: str):
        """
        Creates an appropriate input widget based on the field type.
        """
        # 检查是否是 config_name 字段
        if field_type is str or field_type == Optional[str]:
            if full_field_name.endswith('.config_name'):
                # 从 full_field_name 确定配置类型（database, data_path, prompt）
                config_section = full_field_name.split('.')[-2]  # 获取倒数第二个部分，即配置节名称
                if config_section == 'database':
                    available_configs = self.config_handler.get_global_config().database.available_configs
                elif config_section == 'data_path':
                    available_configs = self.config_handler.get_global_config().data_path.available_configs
                elif config_section == 'prompt':
                    available_configs = self.config_handler.get_global_config().prompt.available_configs
                else:
                    # 如果不是这三个配置节之一，回退到普通文本框
                    available_configs = None

                if available_configs:
                    combo_box = QComboBox()
                    combo_box.addItems(available_configs)
                    return combo_box

            # 定义一些常见的路径字段名称后缀
            path_suffixes = ['_path', '_dir', '_file']
            is_path_field = any(full_field_name.lower().endswith(suffix) for suffix in path_suffixes)

            if is_path_field:
                # 为路径字段创建一个包含 QLineEdit 和 QPushButton 的 QWidget
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(0, 0, 0, 0)
                line_edit = QLineEdit()
                browse_button = QPushButton(_("Browse..."))
                browse_button.clicked.connect(lambda: self._browse_path(line_edit, full_field_name))
                layout.addWidget(line_edit)
                layout.addWidget(browse_button)
                # 在 widget 上存储 line_edit 的引用，以便后续可以访问
                widget.line_edit = line_edit
                return widget
            else:
                return QLineEdit()
        elif field_type is int:
            spin_box = QSpinBox()
            spin_box.setRange(-2147483647, 2147483647) # Max int range
            return spin_box
        elif field_type is float:
            spin_box = QDoubleSpinBox()
            spin_box.setRange(-sys.float_info.max, sys.float_info.max)
            spin_box.setDecimals(3)
            return spin_box
        elif field_type is bool:
            return QCheckBox()
        elif field_type == List[str] or field_type == Optional[List[str]]:
            # For list of strings, use QLineEdit and expect comma-separated values
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(_("Comma-separated values"))
            return line_edit
        elif field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]:
            # For dict of strings, use QLineEdit and expect JSON string
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(_("JSON string (e.g., {\"key\": \"value\"})"))
            return line_edit
        # Add more types as needed (e.g., QComboBox for enums, QFileDialog for paths)
        return None

    def _browse_path(self, line_edit: QLineEdit, full_field_name: str):
        """
        Opens a file dialog to select a path and sets the selected path to the line edit.
        """
        # 确定是选择文件还是目录
        # 这里简单地根据字段名是否包含 'dir' 来判断，实际应用中可能需要更复杂的逻辑
        if 'dir' in full_field_name.lower() or 'directory' in full_field_name.lower():
            path = QFileDialog.getExistingDirectory(self, _("Select Directory"))
        else:
            path, _ = QFileDialog.getOpenFileName(self, _("Select File"))
        
        if path:
            line_edit.setText(path)

    def _on_project_selected(self, project_name: str):
        """
        Handles project selection change, switches project, and reloads config.
        """
        if project_name == self.current_project_name:
            return

        if self.config_handler.switch_project(project_name):
            self.current_project_name = project_name
            self._load_config_values()
            self.project_switched.emit(project_name)
            QMessageBox.information(self, _("Project Switched"), _("Switched to project: {}").format(project_name))
            logging.info(_("Switched to project: {}").format(project_name))
        else:
            QMessageBox.critical(self, _("Project Switch Error"), _("Failed to switch to project: {}").format(project_name))
            self.project_combo.setCurrentText(self.current_project_name) # Revert selection
            logging.error(_("Failed to switch to project: {}").format(project_name))

    def _load_config_values(self):
        """
        Loads current project configuration values into the UI widgets.
        """
        current_config = self.config_handler.get_project_config()
        if current_config:
            self._populate_widgets(current_config, "Project")
            # Update ModelSelectionWidget with current project models
            if current_config.model:
                self.model_selection_widget.set_project_model_names(current_config.model.model_names)
            else:
                self.model_selection_widget.set_project_model_names([])
            # Update PluginSelectionWidget with current project plugin states
            if current_config.plugins and current_config.plugins.plugins:
                plugin_states = {name: p.enabled for name, p in current_config.plugins.plugins.items()}
                self.plugin_selection_widget.set_plugin_states(plugin_states)
            else:
                # If no plugins config, assume all are enabled by default
                all_plugins = self.config_handler.get_plugins_config()
                if all_plugins and all_plugins.plugins:
                    default_states = {name: True for name in all_plugins.plugins.keys()}
                    self.plugin_selection_widget.set_plugin_states(default_states)
                else:
                    self.plugin_selection_widget.set_plugin_states({})
        else:
            logging.warning(_("No project configuration found to load."))
            # Clear widgets if no project config is available
            for widget in self._widgets.values():
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(False)
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(0)
            # Also clear model lists in ModelSelectionWidget and plugin states in PluginSelectionWidget
            self.model_selection_widget.set_project_model_names([])
            self.plugin_selection_widget.set_plugin_states({})


    def _populate_widgets(self, config_obj, prefix: str):
        """
        Recursively populates widgets with values from a config object.
        """
        for field_info in fields(config_obj):
            field_name = field_info.name
            full_field_name = f"{prefix}.{field_name}"
            value = getattr(config_obj, field_name)

            if field_info.type is ProjectPluginsConfig:
                # Plugin selection widget is populated directly in _load_config_values
                pass
            elif field_info.type is ProjectModelConfig:
                # Model selection widget is populated directly in _load_config_values
                pass
            elif is_dataclass(field_info.type):
                self._populate_widgets(value, full_field_name)
            elif full_field_name in self._widgets:
                widget = self._widgets[full_field_name]
                # 检查 widget 是否是包含 QLineEdit 的复合控件
                line_edit = getattr(widget, 'line_edit', None)
                if line_edit and isinstance(line_edit, QLineEdit):
                    # 处理路径字段
                    line_edit.setText(str(value) if value is not None else "")
                elif isinstance(widget, QLineEdit):
                    if field_info.type == List[str] or field_info.type == Optional[List[str]]:
                        widget.setText(", ".join(value) if value else "")
                    elif field_info.type == Dict[str, str] or field_info.type == Optional[Dict[str, str]]:
                        import json
                        widget.setText(json.dumps(value) if value else "")
                    else:
                        widget.setText(str(value) if value is not None else "")
                elif isinstance(widget, QComboBox):
                    # 处理 config_name 字段的下拉框
                    index = widget.findText(str(value) if value is not None else "")
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    else:
                        # 如果值不在选项中，可能需要添加或显示为空
                        widget.setCurrentText(str(value) if value is not None else "")
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value) if value is not None else 0)
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value) if value is not None else 0.0)

    def _save_config_values(self):
        """
        Collects values from UI widgets, validates, and saves them via ConfigHandler.
        """
        new_config_data = self._collect_widget_values(ProjectConfig, "Project")
        
        # Basic validation (can be expanded)
        if not self._validate_collected_data(new_config_data):
            return

        if self.config_handler.save_project_config(new_config_data):
            QMessageBox.information(self, _("Save Successful"), _("Project configuration saved."))
            self.config_saved.emit()
            self.accept() # Closes dialog with accept code
        else:
            QMessageBox.critical(self, _("Save Error"), _("Failed to save project configuration. Check logs for details."))

    def _collect_widget_values(self, config_dataclass, prefix: str) -> Dict[str, Any]:
        """
        Recursively collects values from widgets into a dictionary structure.
        """
        collected_data = {}
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            if field_type is ProjectPluginsConfig:
                # Collect plugin states from PluginSelectionWidget
                plugin_states = self.plugin_selection_widget.get_plugin_states()
                plugin_configs = {}
                project_plugins_config = self.config_handler.get_plugins_config() # Get all available plugins metadata
                if project_plugins_config:
                    for plugin_name, is_enabled in plugin_states.items():
                        existing_plugin_config = project_plugins_config.plugins.get(plugin_name)
                        if existing_plugin_config:
                            plugin_config = PluginConfig(
                                enabled=is_enabled,
                                path=existing_plugin_config.path,
                                module=existing_plugin_config.module,
                                class_name=existing_plugin_config.class_name,
                                settings=existing_plugin_config.settings
                            )
                            plugin_configs[plugin_name] = plugin_config
                        else:
                            # This case should ideally not happen if PluginSelectionWidget is populated correctly
                            plugin_configs[plugin_name] = PluginConfig(enabled=is_enabled)
                collected_data[field_name] = ProjectPluginsConfig(plugins=plugin_configs)
            elif field_type is ProjectModelConfig:
                # Collect selected models from ModelSelectionWidget
                model_names = self.model_selection_widget.get_project_model_names()
                collected_data[field_name] = ProjectModelConfig(model_names=model_names)
            elif is_dataclass(field_type):
                collected_data[field_name] = self._collect_widget_values(field_type, full_field_name)
            elif full_field_name in self._widgets:
                widget = self._widgets[full_field_name]
                value = None
                # 检查 widget 是否是包含 QLineEdit 的复合控件
                line_edit = getattr(widget, 'line_edit', None)
                if line_edit and isinstance(line_edit, QLineEdit):
                    # 处理路径字段
                    text = line_edit.text().strip()
                    value = text if text else None
                elif isinstance(widget, QComboBox):
                    # 处理 config_name 字段的下拉框
                    value = widget.currentText()
                elif isinstance(widget, QLineEdit):
                    text = widget.text().strip()
                    if field_type is int:
                        try:
                            value = int(text)
                        except ValueError:
                            value = None
                    elif field_type is float:
                        try:
                            value = float(text)
                        except ValueError:
                            value = None
                    elif field_type == List[str] or field_type == Optional[List[str]]:
                        value = [item.strip() for item in text.split(',') if item.strip()] if text else []
                    elif field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]:
                        import json
                        try:
                            value = json.loads(text) if text else {}
                        except json.JSONDecodeError:
                            value = None
                    else:
                        value = text if text else None
                elif isinstance(widget, QCheckBox):
                    value = widget.isChecked()
                elif isinstance(widget, QSpinBox):
                    value = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    value = widget.value()
                
                # Handle Optional types: if value is None and field is Optional, keep None
                if getattr(field_type, '__origin__', None) is Union and type(None) in getattr(field_type, '__args__', ()):
                    if value is None:
                        collected_data[field_name] = None
                    else:
                        actual_type = [t for t in field_type.__args__ if t is not type(None)][0]
                        if actual_type == List[str]:
                            collected_data[field_name] = value if isinstance(value, list) else []
                        elif actual_type == Dict[str, str]:
                            collected_data[field_name] = value if isinstance(value, dict) else {}
                        else:
                            collected_data[field_name] = actual_type(value) if value is not None else None
                else:
                    # For non-Optional fields, if value is None, try to use default or raise error
                    if value is None and field_info.default is not MISSING:
                        collected_data[field_name] = field_info.default
                    elif value is None and field_info.default_factory is not MISSING:
                        collected_data[field_name] = field_info.default_factory()
                    else:
                        collected_data[field_name] = value
            else:
                # If widget not found, use default value from schema if available
                if field_info.default is not MISSING:
                    collected_data[field_name] = field_info.default
                elif field_info.default_factory is not MISSING:
                    collected_data[field_name] = field_info.default_factory()
                else:
                    collected_data[field_name] = None

        return collected_data

    def _validate_collected_data(self, data: Dict[str, Any]) -> bool:
        """
        Performs basic validation on the collected data.
        This can be expanded with more specific schema validation.
        """
        # Example: Check if int/float fields were successfully parsed
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    full_field_name = f"Project.{section_name}.{key}"
                    if full_field_name in self._widgets:
                        widget = self._widgets[full_field_name]
                        if isinstance(widget, QLineEdit):
                            field_type = None
                            # Find the actual field type from schema
                            for f_sec in fields(ProjectConfig):
                                if f_sec.name == section_name and is_dataclass(f_sec.type):
                                    for f_item in fields(f_sec.type):
                                        if f_item.name == key:
                                            field_type = f_item.type
                                            break
                                if field_type: break

                            if field_type is int and not isinstance(value, int):
                                QMessageBox.warning(self, _("Validation Error"), _("{field_name} in {section_name} must be an integer.").format(field_name=key, section_name=section_name))
                                return False
                            if field_type is float and not isinstance(value, float):
                                QMessageBox.warning(self, _("Validation Error"), _("{field_name} in {section_name} must be a number.").format(field_name=key, section_name=section_name))
                                return False
                            if (field_type == Dict[str, str] or field_type == Optional[Dict[str, str]]) and not isinstance(value, dict):
                                QMessageBox.warning(self, _("Validation Error"), _("{field_name} in {section_name} must be a valid JSON object.").format(field_name=key, section_name=section_name))
                                return False
        return True
