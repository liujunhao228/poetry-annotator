#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.annotation_reviewer import AnnotationReviewerLogic
from .common_widgets import create_option_frame, configure_grid_row_column


class AnnotationReviewerTab(ttk.Frame):
    """
    诗词标注校对工具的选项卡类。
    """

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        # 初始化逻辑核心
        self.logic = AnnotationReviewerLogic()

        # 初始化界面组件
        self._create_widgets()

        # 初始化一些内部状态
        self.current_poem_info = None
        self.current_sentence_annotations = None
        self.selected_item = None
        
        # ID列表相关状态
        self.id_list = []  # 存储加载的ID列表
        self.current_id_index = -1  # 当前在ID列表中的索引

        # 绑定诗词ID变量变化的追踪器
        self.poem_id_var.trace_add("write", self._on_poem_id_var_change)
        
        # 配置网格权重
        self.rowconfigure(0, weight=0)  # 查询区域
        self.rowconfigure(1, weight=0)  # 诗词信息区域
        self.rowconfigure(2, weight=1)  # 标注详情区域
        self.rowconfigure(3, weight=0)  # 状态栏
        self.columnconfigure(0, weight=1)

    def _create_widgets(self):
        """创建所有 GUI 组件"""
        # 1. 查询区域 (顶部)
        query_frame = create_option_frame(self, "查询条件", (10, 5))
        query_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # 数据库选择
        ttk.Label(query_frame, text="数据库:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.db_var = tk.StringVar()
        self.db_combobox = ttk.Combobox(query_frame, textvariable=self.db_var, width=15, state="readonly")
        self.db_combobox.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self._populate_db_combobox()
        
        # 诗词ID
        ttk.Label(query_frame, text="诗词ID:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.poem_id_var = tk.StringVar()
        self.poem_id_entry = ttk.Entry(query_frame, textvariable=self.poem_id_var, width=15)
        self.poem_id_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        # 绑定回车键到查询功能
        self.poem_id_entry.bind('<Return>', lambda event: self._on_poem_id_change())

        # 模型标识符
        ttk.Label(query_frame, text="模型标识符:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(query_frame, textvariable=self.model_var, width=25, state="readonly")
        self.model_combobox.grid(row=0, column=5, sticky=tk.W, padx=(0, 10))

        # 查询按钮
        self.query_button = ttk.Button(query_frame, text="查询", command=self._on_query)
        self.query_button.grid(row=0, column=6, padx=(0, 10))
        
        # ID列表加载按钮
        self.load_id_list_button = ttk.Button(query_frame, text="加载ID列表", command=self._load_id_list)
        self.load_id_list_button.grid(row=0, column=7, padx=(0, 10))
        
        # 导航按钮
        self.prev_button = ttk.Button(query_frame, text="上一首", command=self._prev_poem, state=tk.DISABLED)
        self.prev_button.grid(row=0, column=8, padx=(0, 5))
        
        self.next_button = ttk.Button(query_frame, text="下一首", command=self._next_poem, state=tk.DISABLED)
        self.next_button.grid(row=0, column=9, padx=(0, 10))
        
        configure_grid_row_column(query_frame, col_weights=[0, 0, 0, 0, 0, 1, 0, 0, 0, 0])

        # 2. 诗词信息展示区域 (中部上方)
        poem_info_frame = create_option_frame(self, "诗词信息", (10, 5))
        poem_info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # 标题和作者信息
        self.poem_info_label = ttk.Label(poem_info_frame, text="标题: N/A    作者: N/A")
        self.poem_info_label.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # 全文显示
        ttk.Label(poem_info_frame, text="全文:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.full_text_widget = scrolledtext.ScrolledText(poem_info_frame, height=3, state=tk.DISABLED)
        self.full_text_widget.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        poem_info_frame.columnconfigure(0, weight=1)  # 让文本框可以随窗口宽度调整

        # 3. 标注结果展示与校对区域 (中部下方 - 主要工作区)
        annotation_frame = create_option_frame(self, "标注详情与校对", (10, 5))
        annotation_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # 创建 Treeview 表格
        columns = ("句子ID", "句子文本", "当前主情感", "当前次情感")
        self.tree = ttk.Treeview(annotation_frame, columns=columns, show='headings', height=10)
        
        # 定义列标题和宽度
        self.tree.heading("句子ID", text="句子ID")
        self.tree.column("句子ID", width=60, anchor=tk.CENTER, stretch=tk.NO)
        
        self.tree.heading("句子文本", text="句子文本")
        self.tree.column("句子文本", width=400, stretch=tk.YES)
        
        self.tree.heading("当前主情感", text="当前主情感")
        self.tree.column("当前主情感", width=120, stretch=tk.NO)
        
        self.tree.heading("当前次情感", text="当前次情感")
        self.tree.column("当前次情感", width=150, stretch=tk.NO)

        # 添加斑马条纹
        self.tree.tag_configure('oddrow', background='#f0f0f0')
        self.tree.tag_configure('evenrow', background='white')

        # 添加滚动条
        tree_scrollbar_y = ttk.Scrollbar(annotation_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set)
        
        tree_scrollbar_x = ttk.Scrollbar(annotation_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=tree_scrollbar_x.set)

        # 布局 Treeview 和滚动条
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        configure_grid_row_column(annotation_frame, row_weights=[1, 0], col_weights=[1, 0])

        # 绑定 Treeview 选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 详细信息/编辑区域 (在列表下方)
        detail_frame = create_option_frame(annotation_frame, "详细信息", (10, 5))
        detail_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        # 详细信息区域可以随窗口高度变化
        annotation_frame.rowconfigure(2, weight=0)  # 保持为0以防止过度扩展，但确保可见性
        
        # 选中句子
        self.selected_sentence_label = ttk.Label(detail_frame, text="选中句子: ")
        self.selected_sentence_label.grid(row=0, column=0, sticky=tk.W)

        # 主情感
        ttk.Label(detail_frame, text="主情感:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.primary_emotion_var = tk.StringVar()
        self.primary_emotion_combobox = ttk.Combobox(
            detail_frame, textvariable=self.primary_emotion_var, 
            width=30, state="readonly"
        )
        self.primary_emotion_combobox.grid(row=2, column=0, sticky=tk.W, pady=(2, 0))
        
        # 次情感
        ttk.Label(detail_frame, text="次情感:").grid(row=1, column=1, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        
        # 创建一个 Frame 来容纳 Listbox 和 Scrollbar
        secondary_frame = ttk.Frame(detail_frame)
        secondary_frame.grid(row=2, column=1, sticky="ew", padx=(20, 0), pady=(2, 0))
        detail_frame.columnconfigure(1, weight=1)  # 让次情感区域可以扩展
        
        self.secondary_listbox = tk.Listbox(secondary_frame, selectmode=tk.MULTIPLE, height=4, exportselection=False)
        secondary_scrollbar = ttk.Scrollbar(secondary_frame, orient=tk.VERTICAL, command=self.secondary_listbox.yview)
        self.secondary_listbox.configure(yscrollcommand=secondary_scrollbar.set)
        
        # 使用 grid 替代 pack 以避免布局管理器冲突
        self.secondary_listbox.grid(row=0, column=0, sticky="nsew")
        secondary_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 配置 secondary_frame 的行列权重
        secondary_frame.rowconfigure(0, weight=1)
        secondary_frame.columnconfigure(0, weight=1)
        
        configure_grid_row_column(detail_frame, col_weights=[0, 1])

        # 填充情感分类下拉框（只初始化一次）
        self._populate_emotion_comboboxes()

        # 4. 状态与操作区域 (底部)
        # 状态信息 (暂时简化处理)
        self.status_label = ttk.Label(self, text="就绪")
        self.status_label.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

    def _populate_emotion_comboboxes(self):
        """填充情感分类下拉框"""
        emotion_list = self.logic.get_full_emotion_list_for_selection(level=2)
        emotion_names = [e['name'] for e in emotion_list]
        self.primary_emotion_combobox['values'] = emotion_names

    def _populate_db_combobox(self):
        """填充数据库下拉框"""
        try:
            db_configs = self.logic.get_available_databases()
            db_names = list(db_configs.keys()) if isinstance(db_configs, dict) else []
            self.db_combobox['values'] = db_names
            if db_names:
                # 默认选择第一个数据库
                self.db_combobox.set(db_names[0])
                # 绑定数据库选择变化事件
                self.db_var.trace_add("write", self._on_db_change)
        except Exception as e:
            print(f"填充数据库下拉框时出错: {e}")

    def _on_db_change(self, *args):
        """当数据库选择改变时的处理函数"""
        db_name = self.db_var.get()
        if db_name:
            # 切换逻辑核心到新的数据库
            self.logic.switch_database(db_name)
            # 清空模型下拉框
            self.model_combobox.set("")
            self.model_combobox['values'] = []
            # 清空诗词ID输入框
            self.poem_id_var.set("")
            # 清空界面显示
            self._clear_display()
            
    def _clear_display(self):
        """清空界面显示"""
        # 清空诗词信息
        self.poem_info_label.config(text="标题: N/A    作者: N/A")
        self.full_text_widget.config(state=tk.NORMAL)
        self.full_text_widget.delete(1.0, tk.END)
        self.full_text_widget.config(state=tk.DISABLED)
        
        # 清空标注表格
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 清空详细信息区域
        self.selected_sentence_label.config(text="选中句子: ")
        self.primary_emotion_var.set("")
        self.secondary_listbox.selection_clear(0, tk.END)

    def _on_poem_id_var_change(self, *args):
        """当诗词ID变量改变时的处理函数（用于追踪变量变化）"""
        # 使用 after 方法延迟执行，避免在用户还在输入时频繁触发
        if hasattr(self, '_after_id'):
            self.master.after_cancel(self._after_id)
        self._after_id = self.master.after(500, self._update_model_combobox)  # 500ms延迟

    def _on_poem_id_change(self):
        """当诗词ID输入框失去焦点或按回车时的处理函数"""
        self._update_model_combobox()
        # 更新导航按钮状态
        self._update_navigation_state_after_manual_input()

    def _update_model_combobox(self):
        """更新模型下拉框"""
        poem_id_str = self.poem_id_var.get().strip()
        if not poem_id_str:
            self.model_combobox['values'] = []
            self.model_var.set("")
            return

        try:
            poem_id = int(poem_id_str)
            models = self.logic.get_available_models_for_poem(poem_id)
            self.model_combobox['values'] = models
            if models:
                self.model_var.set(models[0])  # 默认选择第一个模型
            else:
                self.model_var.set("")
                # 只在用户明确触发查询时显示提示，避免在输入过程中频繁提示
                # messagebox.showinfo("提示", f"诗词ID {poem_id} 没有可用的标注模型")
        except ValueError:
            # 输入的不是有效数字，清空模型列表
            self.model_combobox['values'] = []
            self.model_var.set("")

    def _update_navigation_state_after_manual_input(self):
        """在用户手动输入ID后更新导航状态"""
        if not self.id_list:
            return  # 没有加载ID列表
            
        poem_id_str = self.poem_id_var.get().strip()
        if not poem_id_str:
            self.current_id_index = -1
            self._update_navigation_buttons_state()
            return
            
        try:
            poem_id = int(poem_id_str)
            # 检查输入的ID是否在ID列表中
            if poem_id in self.id_list:
                self.current_id_index = self.id_list.index(poem_id)
            else:
                self.current_id_index = -1  # 不在列表中
        except ValueError:
            self.current_id_index = -1  # 无效ID
            
        self._update_navigation_buttons_state()

    def _on_query(self):
        """处理查询按钮点击事件"""
        db_name = self.db_var.get().strip()
        poem_id_str = self.poem_id_var.get().strip()
        model_id = self.model_var.get().strip()

        if not db_name:
            messagebox.showwarning("输入错误", "请选择数据库")
            return

        if not poem_id_str:
            messagebox.showwarning("输入错误", "请输入诗词ID")
            return

        if not model_id:
            messagebox.showwarning("输入错误", "请选择模型标识符")
            return

        try:
            poem_id = int(poem_id_str)
        except ValueError:
            messagebox.showerror("输入错误", "诗词ID必须是数字")
            return

        # 执行查询
        self.status_label.config(text="查询中...")
        self.master.update_idletasks()  # 更新界面以显示"查询中..."

        poem_info, sentence_annotations = self.logic.query_poem_and_annotation(poem_id, model_id)

        if not poem_info:
            messagebox.showerror("查询失败", f"未找到ID为 {poem_id} 的诗词")
            self.status_label.config(text="错误: 未找到诗词")
            return

        # 更新界面显示
        self._update_poem_info_display(poem_info)
        self._update_annotation_table(sentence_annotations)

        # 保存当前查询结果到内部状态
        self.current_poem_info = poem_info
        self.current_sentence_annotations = sentence_annotations

        # 如果当前ID在ID列表中，更新当前索引
        if self.id_list:
            try:
                self.current_id_index = self.id_list.index(poem_id)
            except ValueError:
                self.current_id_index = -1
            self._update_navigation_buttons_state()

        self.status_label.config(text="查询成功")

    def _load_id_list(self):
        """加载ID列表文件"""
        file_path = filedialog.askopenfilename(
            title="选择ID列表文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return  # 用户取消了选择

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 读取所有行并解析为整数ID
                id_list = []
                for line in f:
                    line = line.strip()
                    if line:  # 跳过空行
                        try:
                            id_list.append(int(line))
                        except ValueError:
                            messagebox.showwarning("格式错误", f"跳过无效ID: {line}")
                
                if not id_list:
                    messagebox.showwarning("加载失败", "ID列表文件为空或没有有效ID")
                    return
                
                # 更新ID列表和相关状态
                self.id_list = id_list
                self.current_id_index = -1  # 重置索引
                self._update_navigation_buttons_state()
                
                messagebox.showinfo("加载成功", f"成功加载 {len(id_list)} 个ID")
                
        except Exception as e:
            messagebox.showerror("加载失败", f"加载ID列表文件时出错: {str(e)}")

    def _prev_poem(self):
        """导航到上一首诗词"""
        if not self.id_list or self.current_id_index <= 0:
            return  # 没有ID列表或已在第一首
            
        self.current_id_index -= 1
        self._navigate_to_current_poem()

    def _next_poem(self):
        """导航到下一首诗词"""
        if not self.id_list or self.current_id_index >= len(self.id_list) - 1:
            return  # 没有ID列表或已在最后一首
            
        self.current_id_index += 1
        self._navigate_to_current_poem()

    def _navigate_to_current_poem(self):
        """导航到当前索引指向的诗词"""
        if not self.id_list or self.current_id_index < 0 or self.current_id_index >= len(self.id_list):
            return  # 索引无效
            
        poem_id = self.id_list[self.current_id_index]
        
        # 更新诗词ID输入框
        self.poem_id_var.set(str(poem_id))
        
        # 自动获取模型并查询
        self._update_model_combobox()
        model_id = self.model_var.get().strip()
        
        if model_id:
            # 自动触发查询
            self._on_query()
        else:
            messagebox.showwarning("查询失败", f"诗词ID {poem_id} 没有可用的标注模型")

    def _update_navigation_buttons_state(self):
        """更新导航按钮的状态"""
        if not self.id_list:
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            return
            
        # 根据当前索引更新按钮状态
        self.prev_button.config(state=tk.NORMAL if self.current_id_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_id_index < len(self.id_list) - 1 else tk.DISABLED)

    def _update_poem_info_display(self, poem_info):
        """更新诗词信息显示区域"""
        display_info = self.logic.format_poem_info_for_display(poem_info)
        
        title = display_info.get('标题', '未知')
        author = display_info.get('作者', '未知')
        self.poem_info_label.config(text=f"标题: {title}    作者: {author}")
        
        # 更新全文显示
        full_text = poem_info.get('full_text', '')
        self.full_text_widget.config(state=tk.NORMAL)
        self.full_text_widget.delete(1.0, tk.END)
        self.full_text_widget.insert(1.0, full_text)
        self.full_text_widget.config(state=tk.DISABLED)

    def _update_annotation_table(self, sentence_annotations):
        """更新标注结果表格"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not sentence_annotations:
            return

        # 格式化数据并插入到表格中
        table_data = self.logic.format_sentence_annotations_for_table(sentence_annotations)
        for i, row_data in enumerate(table_data):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            values = (
                row_data.get("句子ID", ""),
                row_data.get("句子文本", ""),
                row_data.get("当前主情感", ""),
                row_data.get("当前次情感", "")
            )
            self.tree.insert("", tk.END, values=values, tags=(tag,))

    def _on_tree_select(self, event):
        """处理 Treeview 行选择事件"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        item_values = self.tree.item(item, 'values')
        
        if not item_values or len(item_values) < 4:
            return

        # 获取选中行的数据
        sentence_id = item_values[0]
        sentence_text = item_values[1]
        primary_emotion = item_values[2]
        secondary_emotions_str = item_values[3]

        # 更新详细信息区域
        self.selected_sentence_label.config(text=f"选中句子: {sentence_text}")
        
        # 设置主情感下拉框
        self.primary_emotion_var.set(primary_emotion)
        
        # 设置次情感列表框
        self.secondary_listbox.selection_clear(0, tk.END)  # 清除之前的选择
        if secondary_emotions_str != "无":
            emotion_list = self.logic.get_full_emotion_list_for_selection(level=2)
            emotion_names = [e['name'] for e in emotion_list]
            
            secondary_emotions = secondary_emotions_str.split(', ')
            for emotion in secondary_emotions:
                if emotion in emotion_names:
                    index = emotion_names.index(emotion)
                    self.secondary_listbox.selection_set(index)
