# editor_app_refactored.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
from processing_logic_refactored import TextProcessorRefactored

class EmotionEditorAppRefactored:
    def __init__(self, root):
        self.root = root
        self.root.title("情感标注体系专用编辑器 (重构版)")
        self.root.geometry("1200x800")

        self.processor = TextProcessorRefactored()
        self.current_file_path = None
        self.is_modified = False # 自定义修改标志

        # --- 数据模型核心 ---
        # 不再有 self.text_area，而是用结构化数据作为单一事实来源 (Single Source of Truth)
        self.main_content_structure = []  # e.g., [{'id': '01', 'name': '...', 'level': 1}, ...]
        self.mappings_data = {}           # e.g., {'01. 自然山水': 'Nature', ...}

        self._create_menu()
        self._create_tabs()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _set_modified(self, state=True):
        """统一管理编辑状态"""
        if self.is_modified == state:
            return
        self.is_modified = state
        title = self.root.title().replace(" *", "")
        if state:
            self.root.title(f"{title} *")
        else:
            self.root.title(title)

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开 (Open)", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存 (Save)", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出 (Exit)", command=self._on_closing)
        menubar.add_cascade(label="文件 (File)", menu=file_menu)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="重新编号所有类别", command=self.renumber_all)
        menubar.add_cascade(label="工具 (Tools)", menu=tools_menu)
      
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())

    def _create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # 1. 主内容编辑 Tab (全新表格化)
        self._create_structured_editor_tab()
        # 2. 映射表编辑 Tab (保留并与新数据模型集成)
        self._create_mapping_editor_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _create_structured_editor_tab(self):
        """【全新】创建基于Treeview的结构化编辑器"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="主内容结构化编辑")

        # --- 工具栏 ---
        toolbar = ttk.Frame(frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=5)
        ttk.Button(toolbar, text="添加主类", command=self.add_primary_category).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加子类", command=self.add_secondary_category).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除选中", command=self.delete_selected_category).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, padx=5, fill='y')
        ttk.Button(toolbar, text="上移", command=lambda: self.move_item(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="下移", command=lambda: self.move_item(1)).pack(side=tk.LEFT, padx=2)
        
        # --- Treeview 表格 ---
        cols = ('id', 'name', 'description', 'example')
        self.structure_tree = ttk.Treeview(frame, columns=cols, show='headings')
        self.structure_tree.heading('id', text='编号')
        self.structure_tree.heading('name', text='名称')
        self.structure_tree.heading('description', text='解释说明')
        self.structure_tree.heading('example', text='例句')
        self.structure_tree.column('id', width=80, anchor=tk.W)
        self.structure_tree.column('name', width=250, anchor=tk.W)
        self.structure_tree.column('description', width=400, anchor=tk.W)
        self.structure_tree.column('example', width=400, anchor=tk.W)

        # 滚动条
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.structure_tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.structure_tree.configure(yscrollcommand=vsb.set)
        self.structure_tree.pack(expand=True, fill=tk.BOTH)
        
        # 绑定事件
        self.structure_tree.bind('<Double-1>', self._on_structure_tree_double_click)
        self.structure_tree.tag_configure("level1", background='#E8F5E9', font=('Arial', 10, 'bold'))
        self.structure_tree.tag_configure("level2", background='#FFFFFF')

    def _create_mapping_editor_tab(self):
        """创建映射表编辑器（与旧版类似，但数据源不同）"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="表格式映射表编辑")
        
        columns = ('chinese_name', 'english_name')
        self.mapping_tree = ttk.Treeview(frame, columns=columns, show='headings')
        self.mapping_tree.heading('chinese_name', text='原始中文类目 (自动生成)')
        self.mapping_tree.heading('english_name', text='字段命名 (双击编辑)')
        self.mapping_tree.column('chinese_name', width=400, anchor=tk.W)
        self.mapping_tree.column('english_name', width=400, anchor=tk.W)
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.mapping_tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.mapping_tree.pack(expand=True, fill=tk.BOTH)

        self.mapping_tree.bind('<Double-1>', self._on_mapping_tree_double_click)
        self.mapping_tree.tag_configure("level1", background='#E8F5E9')
        self.mapping_tree.tag_configure("level2", background='#FFFFFF')

    # --- 数据填充与同步 ---
    def _populate_structure_tree(self):
        """用 self.main_content_structure 填充主内容表格"""
        for i in self.structure_tree.get_children():
            self.structure_tree.delete(i)
        
        for index, item in enumerate(self.main_content_structure):
            tags = (f"level{item['level']}",)
            # 使用 iid 来存储其在 self.main_content_structure 中的索引
            self.structure_tree.insert("", tk.END, iid=index, values=(
                item['id'], item['name'], item['description'], item['example']
            ), tags=tags)
    
    def _populate_mapping_tree(self):
        """用 self.main_content_structure 和 self.mappings_data 填充映射表"""
        for i in self.mapping_tree.get_children():
            self.mapping_tree.delete(i)
        
        for item in self.main_content_structure:
            full_key = self.processor.get_full_key(item)
            english_name = self.mappings_data.get(full_key, "")
            tags = (f"level{item['level']}",)
            self.mapping_tree.insert("", tk.END, values=(full_key, english_name), tags=tags)

    def _on_tab_change(self, event):
        """切换Tab时，始终从主数据模型刷新视图"""
        selected_tab_idx = self.notebook.index(self.notebook.select())
        if selected_tab_idx == 0:
            self._populate_structure_tree()
        elif selected_tab_idx == 1:
            self._populate_mapping_tree()

    # --- 文件操作 ---
    def open_file(self):
        if self.is_modified:
            if not messagebox.askyesno("警告", "当前有未保存的修改，确定要打开新文件吗？"):
                return

        filepath = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt")])
        if not filepath: return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                full_content = f.read()

            main_content, mapping_md = self.processor.extract_mapping_content(full_content)
            
            # 核心变化：解析为结构化数据
            self.main_content_structure = self.processor.parse_main_content_to_structure(main_content)
            self.mappings_data = self.processor.parse_mapping_from_md(mapping_md)
            
            # 刷新UI
            self._populate_structure_tree()
            self._populate_mapping_tree() # 确保映射表也刷新
            
            self.current_file_path = filepath
            self.root.title(f"情感标注体系专用编辑器 (重构版) - {self.current_file_path}")
            self._set_modified(False)
            self.notebook.select(0) # 默认显示主内容编辑

        except Exception as e:
            messagebox.showerror("打开文件失败", f"无法解析文件，请确认格式是否正确。\n\n错误详情: {e}")

    def save_file(self):
        if not self.current_file_path:
            # 如果没有路径，行为等同于另存为
            filepath = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt")]
            )
            if not filepath: return
            self.current_file_path = filepath
            self.root.title(f"情感标注体系专用编辑器 (重构版) - {self.current_file_path}")
        
        # 校验数据一致性
        validation_errors = self.processor.validate_consistency(self.main_content_structure, self.mappings_data)
        if validation_errors:
            error_message = "保存失败！主内容与映射表不一致：\n\n- " + "\n- ".join(validation_errors)
            if not messagebox.askyesno("校验失败", f"{error_message}\n\n是否仍要强制保存？"):
                return
      
        # 从结构化数据生成文本
        main_content_to_save = self.processor.generate_main_content_from_structure(self.main_content_structure)
        mapping_md_to_save = self.processor.generate_mapping_md(self.main_content_structure, self.mappings_data)
        full_content_to_save = main_content_to_save + "\n\n" + mapping_md_to_save
      
        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(full_content_to_save + "\n")
            messagebox.showinfo("成功", f"文件已保存到:\n{self.current_file_path}")
            self._set_modified(False)
        except Exception as e:
            messagebox.showerror("保存文件失败", str(e))

    # --- 结构化编辑功能 ---
    def add_primary_category(self):
        new_id = f"{len([i for i in self.main_content_structure if i['level'] == 1]) + 1:02d}"
        new_item = {'level': 1, 'id': new_id, 'name': '新的一级类别', 'description': '', 'example': ''}
        self.main_content_structure.append(new_item)
        self._populate_structure_tree()
        self._set_modified()

    def add_secondary_category(self):
        selected_iid = self.structure_tree.focus()
        if not selected_iid:
            messagebox.showwarning("操作无效", "请先选择一个类别，新的子类将添加在其后。")
            return
        
        # 找到父类别ID
        parent_idx = int(selected_iid)
        parent_item = self.main_content_structure[parent_idx]
        while parent_item['level'] != 1:
            parent_idx -= 1
            if parent_idx < 0:
                messagebox.showerror("错误", "无法找到所属的主类别。")
                return
            parent_item = self.main_content_structure[parent_idx]
        
        parent_id_prefix = parent_item['id']
        sub_items_count = len([i for i in self.main_content_structure if i['id'].startswith(parent_id_prefix + '.')])
        new_id = f"{parent_id_prefix}.{sub_items_count + 1:02d}"
        
        new_item = {'level': 2, 'id': new_id, 'name': '新的二级类别', 'description': '描述', 'example': ''}
        
        # 插入到选定项之后
        insert_at_index = int(selected_iid) + 1
        self.main_content_structure.insert(insert_at_index, new_item)
        self._populate_structure_tree()
        self._set_modified()
    
    def delete_selected_category(self):
        selected_iids = self.structure_tree.selection()
        if not selected_iids:
            messagebox.showwarning("操作无效", "请先选择要删除的类别。")
            return
        
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_iids)} 个类别吗？此操作不可撤销。"):
            return
        
        # 从后往前删除，避免索引错乱
        indices_to_delete = sorted([int(iid) for iid in selected_iids], reverse=True)
        for index in indices_to_delete:
            # 如果删除的是主类，也需要考虑删除其子类（可选，当前实现为仅删除选中）
            self.main_content_structure.pop(index)
            
        self._populate_structure_tree()
        self._set_modified()

    def move_item(self, direction): # -1 for up, 1 for down
        selected_iid = self.structure_tree.focus()
        if not selected_iid: return
        
        index = int(selected_iid)
        if direction == -1 and index == 0: return
        if direction == 1 and index == len(self.main_content_structure) - 1: return
        
        new_index = index + direction
        
        # 简单的交换
        item = self.main_content_structure.pop(index)
        self.main_content_structure.insert(new_index, item)
        
        # 移动后需要重新编号以保证逻辑正确性
        self.main_content_structure = self.processor.Renumber_structure(self.main_content_structure)
        self._populate_structure_tree()
        # 选中移动后的项
        self.structure_tree.selection_set(str(new_index))
        self.structure_tree.focus(str(new_index))
        self._set_modified()

    def renumber_all(self):
         if not messagebox.askyesno("确认操作", "确定要对所有类别重新编号吗？这将根据当前顺序更新所有ID。"):
             return
         self.main_content_structure = self.processor.Renumber_structure(self.main_content_structure)
         self._populate_structure_tree()
         self._set_modified()
         messagebox.showinfo("完成","已重新编号！")

    def _on_structure_tree_double_click(self, event):
        """处理主内容表格双击事件"""
        region = self.structure_tree.identify_region(event.x, event.y)
        if region != "cell": return

        item_iid = self.structure_tree.identify_row(event.y)
        column_id_str = self.structure_tree.identify_column(event.x)
        column_index = int(column_id_str.replace('#', '')) - 1
        
        cols = ('id', 'name', 'description', 'example')
        column_name = cols[column_index]

        if column_name == 'id':
            messagebox.showinfo("提示", "编号由程序自动管理，如需调整顺序请使用“上移/下移”后“重新编号”。")
            return
            
        x, y, width, height = self.structure_tree.bbox(item_iid, column_id_str)
        current_value = self.structure_tree.set(item_iid, column_id_str)
        
        entry = ttk.Entry(self.structure_tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.focus_set()
        
        def on_commit(evt):
            new_value = entry.get()
            # 更新数据模型
            item_index = int(item_iid)
            self.main_content_structure[item_index][column_name] = new_value
            # 更新Treeview显示
            self.structure_tree.set(item_iid, column_id_str, new_value)
            self._set_modified()
            entry.destroy()

        entry.bind('<FocusOut>', on_commit)
        entry.bind('<Return>', on_commit)
        entry.bind('<Escape>', lambda e: entry.destroy())

    def _on_mapping_tree_double_click(self, event):
        """处理映射表双击事件 (与旧版类似)"""
        region = self.mapping_tree.identify_region(event.x, event.y)
        if region != "cell": return

        item_id = self.mapping_tree.identify_row(event.y)
        column_id = self.mapping_tree.identify_column(event.x)
      
        if column_id != '#2':
            messagebox.showinfo("提示", "此列自动生成，请在主内容中修改类别名称。")
            return
          
        x, y, width, height = self.mapping_tree.bbox(item_id, column_id)
        current_value = self.mapping_tree.set(item_id, column_id)
      
        entry = ttk.Entry(self.mapping_tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus_set()
      
        def on_commit(evt):
            new_value = entry.get()
            self.mapping_tree.set(item_id, column_id, new_value)
            full_key = self.mapping_tree.set(item_id, '#1')
            self.mappings_data[full_key] = new_value
            self._set_modified()
            entry.destroy()

        entry.bind('<FocusOut>', on_commit)
        entry.bind('<Return>', on_commit)

    def _on_closing(self):
        if self.is_modified:
            if not messagebox.askyesno("退出", "有未保存的修改，确定要退出吗？"):
                return
        self.root.destroy()


if __name__ == "__main__":
    app_root = tk.Tk()
    app = EmotionEditorAppRefactored(app_root)
    app_root.mainloop()
