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
    QComboBox, QScrollArea, QWidget, QListWidget, QListWidgetItem, QGroupBox, QInputDialog,
    QTabWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
from ..config_manager import ConfigHandler
from ..help_texts import HELP_TEXTS
from ..help_window import HelpWindow
from ..i18n_config import translate_config_key
from src.config.schema import ProjectConfig, ProjectLLMConfig, ProjectDatabaseConfig, \
    ProjectDataPathConfig, ProjectPromptConfig, ProjectLoggingConfig, \
    ProjectVisualizerConfig, ProjectModelConfig, ProjectPluginsConfig, PluginConfig, \
    GlobalModelConfigTemplate # Import GlobalModelConfigTemplate for editing
from .llm_model_config_dialog import LLMModelConfigDialog # Import the new dialog

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
        self._plugin_checkboxes = {} # To store references to plugin checkboxes
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
        """
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            # 只处理一级嵌套的数据类
            if is_dataclass(field_type) and field_type not in [ProjectPluginsConfig, ProjectModelConfig]:
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

                # 在滚动区域的内容中构建插件表单
                self._build_plugin_form(form_layout)

                # 将选项卡添加到 QTabWidget
                translated_tab_name = _translate_config_key(field_name)
                self.tab_widget.addTab(tab_content, translated_tab_name)

            elif field_type is ProjectModelConfig:
                # 创建一个新的 QWidget 作为选项卡的内容
                tab_content = QWidget()
                tab_layout = QVBoxLayout(tab_content)
                tab_layout.setSpacing(10)  # Add spacing between elements

                # 在选项卡内容中构建模型管理表单
                self._build_model_selection_form(tab_layout)

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

    def _build_config_form(self, config_dataclass, parent_layout: QFormLayout, prefix: str):
        """
        Recursively builds the form layout for a given dataclass.
        """
        for field_info in fields(config_dataclass):
            field_name = field_info.name
            field_type = field_info.type
            full_field_name = f"{prefix}.{field_name}"

            if field_type is ProjectPluginsConfig:
                # Special handling for plugins
                group_layout = QFormLayout()
                group_label = QLabel(_("<b>Plugin Settings</b>"))
                parent_layout.addRow(group_label)
                parent_layout.addRow(group_layout)
                self._build_plugin_form(group_layout)
            elif field_type is ProjectModelConfig:
                # Special handling for project models
                group_layout = QVBoxLayout()
                group_label = QLabel(_("<b>Project LLM Models</b>"))
                parent_layout.addRow(group_label)
                parent_layout.addRow(group_layout)
                self._build_model_selection_form(group_layout)
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
        # 定义一些常见的路径字段名称后缀
        path_suffixes = ['_path', '_dir', '_file']
        is_path_field = any(full_field_name.lower().endswith(suffix) for suffix in path_suffixes)

        if field_type is str or field_type == Optional[str]:
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

    def _build_plugin_form(self, parent_layout: QFormLayout):
        """
        Builds the form layout specifically for plugins.
        """
        project_plugins_config = self.config_handler.get_plugins_config() # Get all available plugins
        if project_plugins_config:
            for plugin_name in project_plugins_config.plugins.keys():
                checkbox = QCheckBox(plugin_name)
                parent_layout.addRow(checkbox)
                self._plugin_checkboxes[plugin_name] = checkbox

    def _build_model_selection_form(self, parent_layout: QVBoxLayout):
        """
        Builds the UI for selecting and managing project LLM models using a transfer list (穿梭框) pattern.
        """
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(15) # Add spacing between the two lists and buttons

        # Left side: Available Models
        available_models_group_box = QGroupBox(_("Available Models"))
        available_models_layout = QVBoxLayout(available_models_group_box)
        self.available_models_list = QListWidget()
        self.available_models_list.setSelectionMode(QListWidget.ExtendedSelection) # Allow multiple selections
        self.available_models_list.itemDoubleClicked.connect(lambda item: self._edit_model_config(item.text()))
        available_models_layout.addWidget(self.available_models_list)
        
        # Create New Model button for available models
        create_new_model_h_layout = QHBoxLayout()
        create_new_model_h_layout.addStretch()
        self.create_new_model_button = QPushButton(_("Create New Model Configuration"))
        self.create_new_model_button.clicked.connect(self._create_new_model_config)
        create_new_model_h_layout.addWidget(self.create_new_model_button)
        
        self.remove_global_model_button = QPushButton(_("Remove Selected Global Model"))
        self.remove_global_model_button.clicked.connect(self._remove_global_model_config)
        create_new_model_h_layout.addWidget(self.remove_global_model_button)
        create_new_model_h_layout.addStretch()
        available_models_layout.addLayout(create_new_model_h_layout)

        main_h_layout.addWidget(available_models_group_box)

        # Middle: Transfer Buttons
        transfer_buttons_layout = QVBoxLayout()
        transfer_buttons_layout.addStretch()
        self.add_selected_button = QPushButton(" > ")
        self.add_selected_button.clicked.connect(self._add_selected_models_to_project)
        transfer_buttons_layout.addWidget(self.add_selected_button)

        self.remove_selected_button = QPushButton(" < ")
        self.remove_selected_button.clicked.connect(self._remove_selected_models_from_project)
        transfer_buttons_layout.addWidget(self.remove_selected_button)

        self.add_all_button = QPushButton(" >> ")
        self.add_all_button.clicked.connect(self._add_all_models_to_project)
        transfer_buttons_layout.addWidget(self.add_all_button)

        self.remove_all_button = QPushButton(" << ")
        self.remove_all_button.clicked.connect(self._remove_all_models_from_project)
        transfer_buttons_layout.addWidget(self.remove_all_button)
        transfer_buttons_layout.addStretch()
        main_h_layout.addLayout(transfer_buttons_layout)

        # Right side: Project's Active Models
        active_models_group_box = QGroupBox(_("Project's Active Models"))
        active_models_layout = QVBoxLayout(active_models_group_box)
        self.project_models_list = QListWidget()
        self.project_models_list.setSelectionMode(QListWidget.ExtendedSelection) # Allow multiple selections
        self.project_models_list.itemDoubleClicked.connect(lambda item: self._edit_model_config(item.text()))
        active_models_layout.addWidget(self.project_models_list)
        main_h_layout.addWidget(active_models_group_box)
        
        parent_layout.addLayout(main_h_layout)

        # Store a reference to the list widget for later population/collection
        # We will populate both lists in _populate_widgets
        self._widgets["Project.model.model_names"] = self.project_models_list # Still reference the project list for saving

    def _create_new_model_config(self):
        """
        Prompts the user for a new model name and opens the LLMModelConfigDialog for it.
        """
        model_name, ok = QInputDialog.getText(self, _("Create New Model"), _("Enter a name for the new model:"))
        if ok and model_name:
            model_name = model_name.strip()
            if not model_name:
                QMessageBox.warning(self, _("Invalid Name"), _("Model name cannot be empty."))
                return

            # Check if a model with this name already exists globally
            if model_name in self.config_handler.list_all_model_names():
                QMessageBox.warning(self, _("Duplicate Name"), _("A model with the name '{}' already exists. Please choose a different name.").format(model_name))
                return
            
            # Create a default empty config for the new model
            default_config = {field.name: field.default for field in fields(GlobalModelConfigTemplate) if field.default is not MISSING}
            # Ensure provider and model_name are set if they are required and not in default
            if 'provider' not in default_config: default_config['provider'] = ""
            if 'model_name' not in default_config: default_config['model_name'] = model_name # Set default model_name to the new name

            if self.config_handler.save_single_model_config(model_name, default_config):
                QMessageBox.information(self, _("Model Created"), _("New model configuration '{}' created. You can now edit its settings.").format(model_name))
                self._refresh_model_lists() # Refresh both lists
                self._edit_model_config(model_name) # Open dialog to edit the new model
            else:
                QMessageBox.critical(self, _("Error"), _("Failed to create new model configuration."))

    def _remove_global_model_config(self):
        """
        Removes the selected global model configuration.
        """
        selected_items = self.available_models_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, _("No Model Selected"), _("Please select one or more models to remove."))
            return

        model_names_to_remove = [item.text() for item in selected_items]
        
        reply = QMessageBox.question(
            self, _("Remove Models"),
            _("Are you sure you want to remove the selected global model(s)?\n\n{}").format("\n".join(model_names_to_remove)),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            fail_count = 0
            for model_name in model_names_to_remove:
                if self.config_handler.delete_single_model_config(model_name):
                    success_count += 1
                    # Also remove from project_models_list if it's there
                    for i in range(self.project_models_list.count()):
                        item = self.project_models_list.item(i)
                        if item.text() == model_name:
                            self.project_models_list.takeItem(i)
                            break
                else:
                    fail_count += 1
            
            if success_count > 0:
                QMessageBox.information(self, _("Models Removed"), _("{} model(s) removed successfully.").format(success_count))
            if fail_count > 0:
                QMessageBox.critical(self, _("Error"), _("{} model(s) failed to remove. Check logs for details.").format(fail_count))
            
            self._refresh_model_lists() # Refresh both lists

    def _add_selected_models_to_project(self):
        """
        Adds selected models from the available models list to the project's active models list.
        """
        selected_items = self.available_models_list.selectedItems()
        for item in selected_items:
            model_name = item.text()
            # Check if model is already in the project list
            if not self._is_model_in_list(self.project_models_list, model_name):
                self._add_model_item_to_list(self.project_models_list, model_name)
        self._refresh_model_lists() # Refresh both lists to reflect changes

    def _remove_selected_models_from_project(self):
        """
        Removes selected models from the project's active models list.
        """
        selected_items = self.project_models_list.selectedItems()
        for item in selected_items:
            self.project_models_list.takeItem(self.project_models_list.row(item))
        self._refresh_model_lists() # Refresh both lists to reflect changes

    def _add_all_models_to_project(self):
        """
        Adds all models from the available models list to the project's active models list.
        """
        for i in range(self.available_models_list.count()):
            item = self.available_models_list.item(i)
            model_name = item.text()
            if not self._is_model_in_list(self.project_models_list, model_name):
                self._add_model_item_to_list(self.project_models_list, model_name)
        self._refresh_model_lists() # Refresh both lists to reflect changes

    def _remove_all_models_from_project(self):
        """
        Removes all models from the project's active models list.
        """
        self.project_models_list.clear()
        self._refresh_model_lists() # Refresh both lists to reflect changes

    def _is_model_in_list(self, qlist_widget: QListWidget, model_name: str) -> bool:
        """
        Helper to check if a model name exists in a QListWidget.
        """
        for i in range(qlist_widget.count()):
            item = qlist_widget.item(i)
            if item.text() == model_name:
                return True
        return False

    def _add_model_item_to_list(self, qlist_widget: QListWidget, model_name: str):
        """
        Helper to add a model name to a QListWidget.
        """
        # Check if the model already exists in the target list to prevent duplicates
        if not self._is_model_in_list(qlist_widget, model_name):
            item = QListWidgetItem(model_name)
            qlist_widget.addItem(item)

    def _edit_model_config(self, model_name: str):
        """
        Opens a dialog to edit the configuration of a specific model.
        """
        dialog = LLMModelConfigDialog(model_name, self.config_handler, self)
        dialog.config_saved.connect(self._refresh_model_lists) # Refresh if a model config was saved
        dialog.exec_()

    def _refresh_model_lists(self):
        """
        Refreshes both available and project model lists, preserving the current UI state of project models.
        """
        # Get the current (potentially unsaved) list of active models from the UI
        project_active_models = []
        for i in range(self.project_models_list.count()):
            item = self.project_models_list.item(i)
            project_active_models.append(item.text())
        
        # Re-populate both lists based on the current UI state of the project list.
        # The _populate_model_lists method handles clearing the lists.
        self._populate_model_lists(project_active_models)

    def _populate_model_lists(self, project_active_models: Optional[List[str]] = None):
        """
        Populates both the available models list and the project's active models list.
        This implements a "copy" rather than "move" behavior. The available list always
        shows all globally defined models.
        """
        if project_active_models is None:
            project_active_models = []

        all_global_models = set(self.config_handler.list_all_model_names())
        project_active_models_set = set(project_active_models)

        # Populate available models list with ALL global models
        self.available_models_list.clear()
        for model_name in sorted(list(all_global_models)):
            self._add_model_item_to_list(self.available_models_list, model_name)

        # Populate project's active models list
        self.project_models_list.clear()
        for model_name in sorted(list(project_active_models_set)):
            self._add_model_item_to_list(self.project_models_list, model_name)

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
            # Ensure model lists are populated even if ProjectModelConfig is empty
            if not current_config.model or not current_config.model.model_names:
                self._populate_model_lists([])
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
            # Also clear model lists if no config is found
            self.available_models_list.clear()
            self.project_models_list.clear()


    def _populate_widgets(self, config_obj, prefix: str):
        """
        Recursively populates widgets with values from a config object.
        """
        for field_info in fields(config_obj):
            field_name = field_info.name
            full_field_name = f"{prefix}.{field_name}"
            value = getattr(config_obj, field_name)

            if field_info.type is ProjectPluginsConfig:
                # Populate plugin checkboxes
                for plugin_name, checkbox in self._plugin_checkboxes.items():
                    plugin_config: Optional[PluginConfig] = value.plugins.get(plugin_name)
                    if plugin_config:
                        checkbox.setChecked(plugin_config.enabled)
                    else:
                        # If plugin not explicitly in project config, assume enabled by default
                        checkbox.setChecked(True)
            elif field_info.type is ProjectModelConfig:
                # Populate both available and project model lists
                self._populate_model_lists(value.model_names if value else [])
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
                # Collect plugin checkbox values
                plugin_configs = {}
                project_plugins_config = self.config_handler.get_plugins_config() # Get all available plugins metadata
                if project_plugins_config:
                    for plugin_name, checkbox in self._plugin_checkboxes.items():
                        is_enabled = checkbox.isChecked()
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
                            plugin_configs[plugin_name] = PluginConfig(enabled=is_enabled)
                collected_data[field_name] = ProjectPluginsConfig(plugins=plugin_configs)
            elif field_type is ProjectModelConfig:
                # Collect selected models from QListWidget
                model_names = []
                for i in range(self.project_models_list.count()):
                    item = self.project_models_list.item(i)
                    model_names.append(item.text())
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
