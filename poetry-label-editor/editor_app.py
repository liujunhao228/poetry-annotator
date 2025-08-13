import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from processing_logic import TextProcessor

class EmotionEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("情感标注体系专用编辑器")
        self.root.geometry("1000x800")

        self.processor = TextProcessor()
        self.current_file_path = None
      
        # --- 数据模型 ---
        self.categories_data = [] 
        self.mappings_data = {} 

        self._create_menu()
        self._create_tabs()
      
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开 (Open)", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存 (Save)", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为 (Save As...)", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出 (Exit)", command=self._on_closing)
        menubar.add_cascade(label="文件 (File)", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)

        tools_menu.add_command(label="移除类别编号", command=self.apply_clear_numbers)
        tools_menu.add_command(label="移除格式符号", command=self.apply_clear_symbols)
        tools_menu.add_command(label="移除例句", command=self.apply_strip_examples)
        tools_menu.add_separator()      
        tools_menu.add_command(label="一键格式化", command=self.apply_formatting)
        menubar.add_cascade(label="工具 (Tools)", menu=tools_menu)
      
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())

    def _create_toolbar(self, parent_frame):
        """在指定的父组件内创建工具栏"""
        toolbar = tk.Frame(parent_frame, bd=1, relief=tk.RAISED)
      
        self.clear_numbers_btn = tk.Button(toolbar, text="移除编号", command=self.apply_clear_numbers)
        self.clear_numbers_btn.pack(side=tk.LEFT, padx=2, pady=2)
      
        self.clear_symbols_btn = tk.Button(toolbar, text="移除符号", command=self.apply_clear_symbols)
        self.clear_symbols_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.strip_examples_btn = tk.Button(toolbar, text="移除例句", command=self.apply_strip_examples)
        self.strip_examples_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.format_btn = tk.Button(toolbar, text="一键格式化", command=self.apply_formatting)
        self.format_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

    def _create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # 1. 主内容编辑 Tab
        main_editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_editor_frame, text="主内容编辑")

        self._create_toolbar(main_editor_frame)
        
        self.text_area = scrolledtext.ScrolledText(main_editor_frame, wrap=tk.WORD, undo=True, font=("Arial", 12))
        self.text_area.pack(expand=True, fill=tk.BOTH)

        # 2. 映射表编辑 Tab (使用 Treeview)
        self.mapping_editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mapping_editor_frame, text="表格式映射表编辑")
      
        columns = ('chinese_name', 'english_name')
        self.mapping_tree = ttk.Treeview(self.mapping_editor_frame, columns=columns, show='headings')
      
        self.mapping_tree.heading('chinese_name', text='原始中文类目 (不可编辑)')
        self.mapping_tree.heading('english_name', text='字段命名 (双击编辑)')
        self.mapping_tree.column('chinese_name', width=400, anchor=tk.W)
        self.mapping_tree.column('english_name', width=400, anchor=tk.W)
      
        vsb = ttk.Scrollbar(self.mapping_editor_frame, orient="vertical", command=self.mapping_tree.yview)
        self.mapping_tree.configure(yscrollcommand=vsb.set)
      
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.mapping_tree.pack(expand=True, fill=tk.BOTH)

        self.mapping_tree.bind('<Double-1>', self._on_tree_double_click)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
      
        self.text_area.focus_set()

    def _on_tab_change(self, event):
        """当Tab切换时，如果切换到映射表，则更新该表。"""
        current_tab_widget_name = self.notebook.select()
        if self.notebook.nametowidget(current_tab_widget_name) == self.mapping_editor_frame:
            self._populate_mapping_tree()

    def _populate_mapping_tree(self):
        """核心功能：根据主内容动态生成或更新映射表Treeview。"""
        for i in self.mapping_tree.get_children():
            self.mapping_tree.delete(i)
          
        current_main_content = self.text_area.get(1.0, tk.END)
        self.categories_data = self.processor.parse_categories_from_main_content(current_main_content)
      
        if not self.categories_data:
            messagebox.showinfo("提示", "主内容区未检测到有效类别，无法生成映射表。")
            return
          
        for category in self.categories_data:
            full_key = category['full_key']
            english_name = self.mappings_data.get(full_key, "")
            self.mapping_tree.insert("", tk.END, values=(full_key, english_name), tags=(f"level{category['level']}",))
      
        self.mapping_tree.tag_configure("level1", background='#E8F5E9')
        self.mapping_tree.tag_configure("level2", background='#FFFFFF')

    def _on_tree_double_click(self, event):
        """处理Treeview双击事件，弹出编辑框。"""
        region = self.mapping_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        item_id = self.mapping_tree.identify_row(event.y)
        column_id = self.mapping_tree.identify_column(event.x)
      
        if column_id != '#2':
            messagebox.showinfo("提示", "此列不可编辑，请在“主内容编辑”Tab中修改类别名称。")
            return
          
        x, y, width, height = self.mapping_tree.bbox(item_id, column_id)
        current_value = self.mapping_tree.set(item_id, column_id)
      
        entry = ttk.Entry(self.mapping_tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.focus_set()
      
        def on_commit(evt):
            new_value = entry.get()
            self.mapping_tree.set(item_id, column_id, new_value)
          
            full_key = self.mapping_tree.set(item_id, '#1')
            self.mappings_data[full_key] = new_value
            self.text_area.edit_modified(True)
          
            entry.destroy()

        entry.bind('<FocusOut>', on_commit)
        entry.bind('<Return>', on_commit)
        entry.bind('<Escape>', lambda e: entry.destroy())

    def open_file(self):
        if self.text_area.edit_modified(): 
            if not messagebox.askyesno("警告", "当前有未保存的修改，打开新文件会丢失这些修改。确定要继续吗？"):
                return

        filepath = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt")])
        if not filepath: return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                full_content = f.read()

            main_content, mapping_md = self.processor.extract_mapping_content(full_content)
          
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, main_content)
          
            self.mappings_data = self.processor.parse_mapping_from_md(mapping_md)
          
            self.current_file_path = filepath
            self.root.title(f"情感标注体系专用编辑器 - {self.current_file_path}")
            self.text_area.edit_modified(False)
            self.notebook.select(0)

        except Exception as e:
            messagebox.showerror("打开文件失败", str(e))

    def save_file(self):
        if not self.current_file_path:
            self.save_as_file()
        else:
            self._write_to_file(self.current_file_path)

    def save_as_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt")]
        )
        if filepath:
            self._write_to_file(filepath)
            self.current_file_path = filepath
            self.root.title(f"情感标注体系专用编辑器 - {self.current_file_path}")

    def _write_to_file(self, filepath):
        """核心保存逻辑：校验、合并、写入。"""
        main_content_to_save = self.text_area.get(1.0, tk.END).strip()
        final_categories = self.processor.parse_categories_from_main_content(main_content_to_save)
      
        validation_errors = self.processor.validate_consistency(final_categories, self.mappings_data)
        if validation_errors:
            error_message = "保存失败！主内容与映射表不一致：\n\n- " + "\n- ".join(validation_errors)
            messagebox.showerror("校验失败", error_message)
            return
      
        mapping_md_to_save = self.processor.generate_mapping_md(final_categories, self.mappings_data)
        full_content_to_save = main_content_to_save + "\n\n" + mapping_md_to_save
      
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_content_to_save + "\n")
          
            messagebox.showinfo("成功", f"文件已保存到:\n{filepath}")
            self.text_area.edit_modified(False)
        except Exception as e:
            messagebox.showerror("保存文件失败", str(e))

    def _perform_text_operation(self, operation_func, confirm_msg):
        """通用文本操作执行器。"""
        if not messagebox.askyesno("确认操作", confirm_msg):
            return
      
        current_text = self.text_area.get(1.0, tk.END)
        # 注意：新逻辑函数已内置extract_mapping_content，此处传递完整文本
        processed_text = operation_func(current_text)
      
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, processed_text)
        self.text_area.edit_modified(True)
        messagebox.showinfo("完成", "操作已完成！")

    def apply_clear_numbers(self):
        """调用 processor 来仅移除主内容区的类别编号"""
        self._perform_text_operation(
            self.processor.clear_numbers,
            "这将仅从主内容区移除所有类别编号 (如 '01.', '01.01 ')。\n确定要继续吗？"
        )

    def apply_clear_symbols(self):
        """调用 processor 来仅移除主内容区的 Markdown 符号"""
        self._perform_text_operation(
            self.processor.clear_special_symbols,
            "这将仅从主内容区移除所有Markdown格式化符号 (如 ####, **, -)。\n确定要继续吗？"
        )

    def apply_strip_examples(self):
        # 注意: _perform_text_operation 的逻辑略有不同。此处为保持行为一致性，我们手动实现
        if not messagebox.askyesno("确认操作", "这将从主内容中移除所有括号（...）内的例句。\n确定要继续吗？"):
            return
      
        current_text = self.text_area.get(1.0, tk.END)
        processed_text = self.processor.remove_examples(current_text)
      
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, processed_text)
        self.text_area.edit_modified(True)
        messagebox.showinfo("完成", "操作已完成！")

    def apply_formatting(self):
        # 注意: _perform_text_operation 的逻辑略有不同。此处为保持行为一致性，我们手动实现
         if not messagebox.askyesno("确认操作", "这将根据当前主内容的纯文本，自动编号并生成最终的Markdown格式。\n确定要继续吗？"):
            return
      
         current_text = self.text_area.get(1.0, tk.END)
         processed_text = self.processor.format_for_saving(current_text)
      
         self.text_area.delete(1.0, tk.END)
         self.text_area.insert(tk.END, processed_text)
         self.text_area.edit_modified(True)
         messagebox.showinfo("完成", "操作已完成！")
  
    def _on_closing(self):
        if self.text_area.edit_modified():
            if not messagebox.askyesno("退出", "有未保存的修改，确定要退出吗？"):
                return
        self.root.destroy()

if __name__ == "__main__":
    app_root = tk.Tk()
    app = EmotionEditorApp(app_root)
    app_root.mainloop()