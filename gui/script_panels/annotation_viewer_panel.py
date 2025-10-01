import logging
import json
from typing import List, Dict, Any # Import List and Dict for type hints
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, 
    QFormLayout, QMessageBox, QComboBox, QScrollArea, QGroupBox, QGridLayout, QFileDialog
)
from PyQt5.QtCore import pyqtSignal, Qt
from src.plugin_system.manager import PluginManager
from src.data.models import Poem # 导入 Poem 模型
from src.annotation_reviewer import AnnotationReviewerLogic # 导入 AnnotationReviewerLogic
from gui.i18n import _ # 从 gui.i18n 导入 _

logger = logging.getLogger(__name__)

class AnnotationViewerPanel(QWidget):
    """
    GUI panel for viewing and editing poem annotations.
    """
    poem_loaded = pyqtSignal(int) # Signal emitted when a poem is loaded

    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.social_poem_analysis_plugin = self.plugin_manager.get_plugin("social_poem_analysis")
        if not self.social_poem_analysis_plugin:
            raise RuntimeError("SocialPoemAnalysisPlugin not found. Ensure it is loaded.")
        
        # 初始化 AnnotationReviewerLogic，传入 social_poem_analysis_plugin 实例
        self.annotation_reviewer_logic = AnnotationReviewerLogic(self.social_poem_analysis_plugin)

        self.current_poem_id = None
        self.current_model_identifier = "default" # Default annotation source
        self.current_poem_data = None # 存储 Poem 实例
        self.annotation_widgets = [] # To keep track of dynamically created annotation widgets
        self.poem_id_list: List[int] = [] # Stores poem IDs loaded from a file
        self.current_list_index: int = -1 # Current position in the poem_id_list

        self.setup_ui()

    def setup_ui(self):
        """
        Builds the UI for the Annotation Viewer and Editor.
        """
        main_layout = QVBoxLayout(self)

        # Top Section: Poem Search and Navigation
        search_group = QGroupBox(_("Poem Selection"))
        search_layout = QHBoxLayout()
        
        self.poem_id_input = QLineEdit()
        self.poem_id_input.setPlaceholderText(_("Enter Poem ID"))
        search_layout.addWidget(QLabel(_("Poem ID:")))
        search_layout.addWidget(self.poem_id_input)

        self.search_button = QPushButton(_("Search by ID"))
        self.search_button.clicked.connect(self._search_poem_by_id)
        search_layout.addWidget(self.search_button)
        
        self.load_ids_button = QPushButton(_("Load ID List"))
        self.load_ids_button.clicked.connect(self._load_id_list_from_file)
        search_layout.addWidget(self.load_ids_button)

        self.prev_button = QPushButton(_("Previous Poem"))
        self.prev_button.clicked.connect(self._load_previous_poem)
        search_layout.addWidget(self.prev_button)

        self.next_button = QPushButton(_("Next Poem"))
        self.next_button.clicked.connect(self._load_next_poem)
        search_layout.addWidget(self.next_button)
        
        self.list_position_label = QLabel(_("List Position: (N/A)"))
        search_layout.addWidget(self.list_position_label)

        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # Poem Info and Annotation Source
        info_layout = QHBoxLayout()
        self.poem_title_label = QLabel(_("Title: "))
        self.poem_author_label = QLabel(_("Author: "))
        self.poem_id_label = QLabel(_("ID: "))
        info_layout.addWidget(self.poem_id_label)
        info_layout.addWidget(self.poem_title_label)
        info_layout.addWidget(self.poem_author_label)
        info_layout.addStretch(1)

        self.model_selector_label = QLabel(_("Annotation Source:"))
        self.model_selector_combo = QComboBox()
        self.model_selector_combo.currentIndexChanged.connect(self._on_model_selected)
        info_layout.addWidget(self.model_selector_label)
        info_layout.addWidget(self.model_selector_combo)
        main_layout.addLayout(info_layout)

        # Middle Section: Poem Content and Annotation Editor
        content_editor_layout = QHBoxLayout()

        # Left: Poem Content Display
        poem_content_group = QGroupBox(_("Poem Content"))
        poem_content_layout = QVBoxLayout()
        self.poem_text_display = QTextEdit()
        self.poem_text_display.setReadOnly(True)
        self.poem_text_display.setPlaceholderText(_("Poem content will appear here..."))
        poem_content_layout.addWidget(self.poem_text_display)
        poem_content_group.setLayout(poem_content_layout)
        content_editor_layout.addWidget(poem_content_group, 1)

        # Right: Annotation Editor
        annotation_editor_group = QGroupBox(_("Annotation Editor"))
        self.annotation_scroll_area = QScrollArea()
        self.annotation_scroll_area.setWidgetResizable(True)
        self.annotation_content_widget = QWidget()
        self.annotation_content_layout = QVBoxLayout(self.annotation_content_widget)
        self.annotation_scroll_area.setWidget(self.annotation_content_widget)
        annotation_editor_group.setLayout(QVBoxLayout())
        annotation_editor_group.layout().addWidget(self.annotation_scroll_area)
        content_editor_layout.addWidget(annotation_editor_group, 2) # Give more space to editor

        main_layout.addLayout(content_editor_layout)

        # Bottom Section: Action Buttons
        action_layout = QHBoxLayout()
        self.save_button = QPushButton(_("Save Annotations"))
        self.save_button.clicked.connect(self._save_annotations)
        action_layout.addWidget(self.save_button)

        self.reload_button = QPushButton(_("Reload Annotations"))
        self.reload_button.clicked.connect(self._reload_annotations)
        action_layout.addWidget(self.reload_button)
        
        main_layout.addLayout(action_layout)

        self._update_ui_state(False) # Initially disable editing features

    def _update_ui_state(self, enable: bool):
        """Enables/disables UI elements based on whether a poem is loaded."""
        self.save_button.setEnabled(enable)
        self.reload_button.setEnabled(enable)
        self.model_selector_combo.setEnabled(enable)
        for widget in self.annotation_widgets:
            widget.setEnabled(enable)

    def _search_poem_by_id(self):
        """Searches for a poem by ID and loads it."""
        poem_id_text = self.poem_id_input.text().strip()
        if not poem_id_text:
            QMessageBox.warning(self, _("Input Error"), _("Please enter a Poem ID."))
            return
        
        try:
            poem_id = int(poem_id_text)
            self._load_poem(poem_id)
        except ValueError:
            QMessageBox.warning(self, _("Input Error"), _("Invalid Poem ID. Please enter a number."))
        
        # Clear the ID list if a manual search is performed
        self.poem_id_list = []
        self.current_list_index = -1
        self._update_list_position_label()

    def _load_id_list_from_file(self):
        """Opens a file dialog to load a list of poem IDs from a text file."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle(_("Load Poem ID List"))
        file_dialog.setNameFilter(_("Text files (*.txt);;All files (*.*)"))
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        raw_ids = f.readlines()
                        
                    new_id_list = []
                    for line in raw_ids:
                        line = line.strip()
                        if line:
                            try:
                                poem_id = int(line)
                                new_id_list.append(poem_id)
                            except ValueError:
                                logger.warning(f"Skipping invalid ID in file: {line}")
                                
                    if new_id_list:
                        self.poem_id_list = new_id_list
                        self.current_list_index = 0
                        self._load_poem(self.poem_id_list[self.current_list_index])
                        QMessageBox.information(self, _("Load Successful"), _("Loaded {} poem IDs from {}").format(len(self.poem_id_list), file_path))
                    else:
                        QMessageBox.warning(self, _("Load Failed"), _("No valid poem IDs found in the selected file."))
                        self.poem_id_list = []
                        self.current_list_index = -1
                    self._update_list_position_label()

                except Exception as e:
                    logger.error(f"Error loading ID list from file {file_path}: {e}")
                    QMessageBox.critical(self, _("File Error"), _("Failed to load ID list from file: {}").format(str(e)))

    def _update_list_position_label(self):
        """Updates the label showing current position in the ID list."""
        if self.poem_id_list and self.current_list_index != -1:
            self.list_position_label.setText(_("List Position: ({}/{})").format(self.current_list_index + 1, len(self.poem_id_list)))
            self.prev_button.setEnabled(self.current_list_index > 0)
            self.next_button.setEnabled(self.current_list_index < len(self.poem_id_list) - 1)
        else:
            self.list_position_label.setText(_("List Position: (N/A)"))
            self.prev_button.setEnabled(self.current_poem_id is not None) # Enable if a single poem is loaded
            self.next_button.setEnabled(self.current_poem_id is not None) # Enable if a single poem is loaded

    def _load_poem(self, poem_id: int):
        """Loads poem data and its annotations."""
        logger.info(f"Loading poem ID: {poem_id}")
        
        # 使用 AnnotationReviewerLogic 获取诗词信息
        # 避免覆盖全局的 _ 翻译函数
        poem_info, annotations_data = self.annotation_reviewer_logic.query_poem_and_annotation(poem_id, self.current_model_identifier)
        
        if poem_info:
            self.current_poem_id = poem_id
            # 将 poem_info 转换为 Poem 模型实例，以便保持 current_poem_data 的类型一致性
            self.current_poem_data = Poem(
                id=poem_info['id'],
                title=poem_info['title'],
                author=poem_info['author'],
                paragraphs=poem_info['paragraphs'],
                full_text=poem_info['full_text']
            )
            self.poem_id_label.setText(_("ID: {}").format(self.current_poem_data.id))
            self.poem_title_label.setText(_("Title: {}").format(self.current_poem_data.title))
            self.poem_author_label.setText(_("Author: {}").format(self.current_poem_data.author))
            self.poem_text_display.setText("\n".join(self.current_poem_data.paragraphs))
            self._update_ui_state(True)
            self._populate_model_selector()
            self.poem_loaded.emit(poem_id) # Emit signal
            logger.info(f"Poem ID {poem_id} loaded and UI updated.")
        else:
            logger.warning(f"Poem object is None for ID {poem_id}, displaying warning message.")
            QMessageBox.warning(self, _("Poem Not Found"), _("No poem found with ID: {}").format(poem_id))
            self._clear_ui()
            self._update_ui_state(False)

    def _clear_ui(self):
        """Clears all UI fields."""
        self.poem_id_label.setText(_("ID: "))
        self.poem_title_label.setText(_("Title: "))
        self.poem_author_label.setText(_("Author: "))
        self.poem_text_display.clear()
        self.model_selector_combo.clear()
        self._clear_annotation_editor()
        self.current_poem_id = None
        self.current_poem_data = None
        self.current_model_identifier = "default"
        self.poem_id_list = [] # Clear list on UI clear
        self.current_list_index = -1
        self._update_list_position_label()

    def _populate_model_selector(self):
        """Populates the model selector with available annotation sources."""
        self.model_selector_combo.clear()
        if self.current_poem_id is not None:
            # 使用 AnnotationReviewerLogic 获取可用模型
            sources = self.annotation_reviewer_logic.get_available_models_for_poem(self.current_poem_id)
            # Add a "New Annotation" option
            self.model_selector_combo.addItem(_("New Annotation"), "new_annotation")
            for source in sources:
                self.model_selector_combo.addItem(source, source)
            
            # Try to select the default or first available source
            # Find the index of the current_model_identifier if it exists in the combo box
            index_to_select = -1
            for i in range(self.model_selector_combo.count()):
                if self.model_selector_combo.itemData(i) == self.current_model_identifier:
                    index_to_select = i
                    break
            
            if index_to_select != -1:
                self.model_selector_combo.setCurrentIndex(index_to_select)
            elif sources:
                # If current_model_identifier is not found, and there are other sources, select the first one (after "New Annotation")
                self.model_selector_combo.setCurrentIndex(1) 
                self.current_model_identifier = self.model_selector_combo.itemData(1)
            else:
                # If no sources, select "New Annotation"
                self.model_selector_combo.setCurrentIndex(0) 
                self.current_model_identifier = "new_annotation"
            
            # Ensure annotations are loaded after selection is set
            self._load_annotations_for_current_model()

    def _on_model_selected(self, index: int):
        """Handles selection change in the model selector."""
        # Only proceed if the current_poem_id is set, otherwise it's an initial clear/populate
        if self.current_poem_id is not None and index >= 0:
            selected_model = self.model_selector_combo.itemData(index)
            if selected_model and selected_model != self.current_model_identifier: # Only reload if selection actually changed
                self.current_model_identifier = selected_model
                self._load_annotations_for_current_model()

    def _load_annotations_for_current_model(self):
        """Loads annotations for the currently selected poem and model."""
        self._clear_annotation_editor()
        if self.current_poem_id is None or self.current_poem_data is None:
            return

        annotations = []
        if self.current_model_identifier != "new_annotation":
            # 使用 AnnotationReviewerLogic 获取标注数据
            _, annotations_from_logic = self.annotation_reviewer_logic.query_poem_and_annotation(
                self.current_poem_id, self.current_model_identifier
            )
            if annotations_from_logic:
                annotations = annotations_from_logic
        
        # _display_annotations 期望的 annotations 格式是 SentenceAnnotation 列表
        # AnnotationReviewerLogic._process_sentence_annotations 已经将其转换为该格式
        self._display_annotations(self.current_poem_data.paragraphs, annotations)

    def _clear_annotation_editor(self):
        """Clears all dynamically created annotation widgets."""
        for widget in self.annotation_widgets:
            widget.deleteLater()
        self.annotation_widgets.clear()
        # Clear any remaining widgets in the layout
        while self.annotation_content_layout.count():
            item = self.annotation_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _display_annotations(self, paragraphs: List[str], annotations: List[Dict[str, Any]]):
        """
        Displays annotation widgets for each sentence.
        If no annotation exists for a sentence, it creates an empty one.
        """
        self._clear_annotation_editor() # Ensure clean slate

        # Map existing annotations by sentence_id for easy lookup
        annotations_map = {ann['sentence_id']: ann for ann in annotations}

        # Get categories from AnnotationReviewerLogic
        categories_data = self.annotation_reviewer_logic.get_all_emotion_categories()
        
        for i, sentence_text in enumerate(paragraphs):
            sentence_id = f"S{i+1}"
            existing_annotation = annotations_map.get(sentence_id, {})

            sentence_group = QGroupBox(f"{_('Sentence')} {sentence_id}: {sentence_text}")
            sentence_layout = QFormLayout()

            # Relationship Action
            ra_combo = QComboBox()
            ra_combo.addItem(_("Select..."), "")
            for cat in categories_data["relationship_action"]["categories"]:
                # Use name_zh if available, otherwise fall back to name or id
                display_name = cat.get('name_zh', cat.get('name', cat['id']))
                ra_combo.addItem(f"{cat['id']} - {display_name}", cat['id'])
            # Set current item by data instead of text to be more robust
            if existing_annotation.get('relationship_action'):
                idx = ra_combo.findData(existing_annotation['relationship_action'])
                if idx != -1:
                    ra_combo.setCurrentIndex(idx)
            sentence_layout.addRow(QLabel(_("Relationship Action:")), ra_combo)

            # Emotional Strategy
            es_combo = QComboBox()
            es_combo.addItem(_("Select..."), "")
            for cat in categories_data["emotional_strategy"]["categories"]:
                # Use name_zh if available, otherwise fall back to name or id
                display_name = cat.get('name_zh', cat.get('name', cat['id']))
                es_combo.addItem(f"{cat['id']} - {display_name}", cat['id'])
            # Set current item by data instead of text to be more robust
            if existing_annotation.get('emotional_strategy'):
                idx = es_combo.findData(existing_annotation['emotional_strategy'])
                if idx != -1:
                    es_combo.setCurrentIndex(idx)
            sentence_layout.addRow(QLabel(_("Emotional Strategy:")), es_combo)

            # Communication Scene (Multi-select, using checkboxes or similar, for now just a QLineEdit)
            # For simplicity, let's use a QLineEdit for now, expecting comma-separated values
            # A more robust solution would involve a custom widget with checkboxes.
            cs_input = QLineEdit()
            cs_input.setPlaceholderText(_("Comma-separated SC codes (e.g., SC01, SC03)"))
            if existing_annotation.get('communication_scene'):
                # communication_scene is a list, join it for display
                cs_input.setText(", ".join(existing_annotation['communication_scene']))
            sentence_layout.addRow(QLabel(_("Communication Scene:")), cs_input)

            # Risk Level
            rl_combo = QComboBox()
            rl_combo.addItem(_("Select..."), "")
            for cat in categories_data["risk_level"]["categories"]:
                # Use name_zh if available, otherwise fall back to name or id
                display_name = cat.get('name_zh', cat.get('name', cat['id']))
                rl_combo.addItem(f"{cat['id']} - {display_name}", cat['id'])
            # Set current item by data instead of text to be more robust
            if existing_annotation.get('risk_level'):
                idx = rl_combo.findData(existing_annotation['risk_level'])
                if idx != -1:
                    rl_combo.setCurrentIndex(idx)
            sentence_layout.addRow(QLabel(_("Risk Level:")), rl_combo)

            # Rationale
            rationale_input = QLineEdit()
            rationale_input.setPlaceholderText(_("Brief rationale (max 25 chars)"))
            if existing_annotation.get('rationale'):
                rationale_input.setText(existing_annotation['rationale'])
            sentence_layout.addRow(QLabel(_("Rationale:")), rationale_input)

            sentence_group.setLayout(sentence_layout)
            self.annotation_content_layout.addWidget(sentence_group)
            self.annotation_widgets.append(sentence_group) # Store the group box

            # Store references to the input widgets for later retrieval
            sentence_group.setProperty("sentence_id", sentence_id)
            sentence_group.setProperty("ra_combo", ra_combo)
            sentence_group.setProperty("es_combo", es_combo)
            sentence_group.setProperty("cs_input", cs_input)
            sentence_group.setProperty("rl_combo", rl_combo)
            sentence_group.setProperty("rationale_input", rationale_input)

        self.annotation_content_layout.addStretch(1) # Push content to top

    def _collect_annotations_from_ui(self) -> List[Dict[str, Any]]:
        """Collects annotation data from UI widgets."""
        collected_annotations = []
        for group_box in self.annotation_widgets:
            sentence_id = group_box.property("sentence_id")
            ra_combo = group_box.property("ra_combo")
            es_combo = group_box.property("es_combo")
            cs_input = group_box.property("cs_input")
            rl_combo = group_box.property("rl_combo")
            rationale_input = group_box.property("rationale_input")

            communication_scene_list = []
            cs_text = cs_input.text().strip()
            if cs_text:
                communication_scene_list = [c.strip() for c in cs_text.split(',') if c.strip()]

            annotation = {
                "sentence_uid": sentence_id, # 插件期望 sentence_uid
                "sentence_index": int(sentence_id[1:]) - 1, # 从 S1, S2... 提取索引
                "sentence_text": self.current_poem_data.paragraphs[int(sentence_id[1:]) - 1], # 从当前诗词数据中获取句子文本
                "relationship_action": ra_combo.currentData() if ra_combo.currentData() and ra_combo.currentData() != "" else None,
                "emotional_strategy": es_combo.currentData() if es_combo.currentData() and es_combo.currentData() != "" else None,
                "communication_scene": communication_scene_list,
                "risk_level": rl_combo.currentData() if rl_combo.currentData() and rl_combo.currentData() != "" else None,
                "rationale": rationale_input.text().strip()
            }
            collected_annotations.append(annotation)
        return collected_annotations

    def _save_annotations(self):
        """Saves the current annotations to the database."""
        if self.current_poem_id is None:
            QMessageBox.warning(self, _("No Poem Loaded"), _("Please load a poem before saving annotations."))
            return

        annotations_to_save = self._collect_annotations_from_ui()
        
        # Validate collected annotations (basic check)
        for ann in annotations_to_save:
            if not ann["relationship_action"] or not ann["emotional_strategy"] or not ann["risk_level"]:
                QMessageBox.warning(self, _("Validation Error"), _("Please select all required annotation fields for each sentence."))
                return
            if not ann["rationale"]:
                QMessageBox.warning(self, _("Validation Error"), _("Please provide a rationale for each sentence."))
                return
            if len(ann["rationale"]) > 25:
                QMessageBox.warning(self, _("Validation Error"), _("Rationale for sentence {} exceeds 25 characters.").format(ann["sentence_id"]))
                return

        try:
            import asyncio
            # Use asyncio.run to run the async plugin method from a sync context
            success = asyncio.run(self.social_poem_analysis_plugin.update_annotations(
                self.current_poem_id, self.current_model_identifier, annotations_to_save
            ))
            if success:
                QMessageBox.information(self, _("Save Successful"), _("Annotations saved successfully!"))
                self._load_annotations_for_current_model() # Reload to show saved state
            else:
                QMessageBox.critical(self, _("Save Failed"), _("Failed to save annotations."))
        except Exception as e:
            logger.error(f"Error saving annotations: {e}")
            QMessageBox.critical(self, _("Error"), _("An error occurred while saving annotations: {}").format(str(e)))

    def _reload_annotations(self):
        """Reloads annotations from the database, discarding unsaved changes."""
        if self.current_poem_id is None:
            QMessageBox.warning(self, _("No Poem Loaded"), _("Please load a poem first."))
            return
        self._load_annotations_for_current_model()
        QMessageBox.information(self, _("Reload Complete"), _("Annotations reloaded from database."))

    def _load_previous_poem(self):
        """Loads the previous poem based on current ID or navigates the ID list."""
        if self.poem_id_list and self.current_list_index > 0:
            self.current_list_index -= 1
            self._load_poem(self.poem_id_list[self.current_list_index])
            self._update_list_position_label()
        elif self.current_poem_id is not None and not self.poem_id_list: # Fallback to single poem navigation
            self._load_poem(self.current_poem_id - 1)
            self._update_list_position_label()
        else:
            QMessageBox.information(self, _("Navigation"), _("No previous poem in list or no poem loaded."))

    def _load_next_poem(self):
        """Loads the next poem based on current ID or navigates the ID list."""
        if self.poem_id_list and self.current_list_index < len(self.poem_id_list) - 1:
            self.current_list_index += 1
            self._load_poem(self.poem_id_list[self.current_list_index])
            self._update_list_position_label()
        elif self.current_poem_id is not None and not self.poem_id_list: # Fallback to single poem navigation
            self._load_poem(self.current_poem_id + 1)
            self._update_list_position_label()
        else:
            QMessageBox.information(self, _("Navigation"), _("No next poem in list or no poem loaded."))
