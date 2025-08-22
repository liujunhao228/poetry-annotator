#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置编辑器 GUI 程序
用于简化编辑 poetry-annotator 项目配置文件 (.ini) 的体验

该程序支持新的配置目录结构：
config/
└── projects/
    ├── tangshi/
    │   └── project.ini               # 唐诗项目配置
    ├── songci/
    │   └── project.ini               # 宋词项目配置
    └── default/
        └── project.ini               # 默认项目配置
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import configparser
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径，确保能正确导入 src 下的模块
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class ProjectConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("诗歌标注工具 - 项目配置编辑器 (重构版)")
        self.root.geometry("800x600")
        
        # 初始化配置解析器
        self.config = configparser.ConfigParser()
        self.current_file_path = None
        
        # 创建界面
        self.create_menu()
        self.create_notebook()
        self.create_status_bar()
        
        # 设置关闭窗口时的回调
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开项目配置", command=self.open_config)
        file_menu.add_command(label="保存", command=self.save_config, state="disabled")
        file_menu.add_command(label="另存为...", command=self.save_config_as, state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 保存菜单引用以便后续更新状态
        self.file_menu = file_menu
    
    def create_notebook(self):
        """创建标签页控件"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_menu_state(self, state):
        """更新文件菜单中保存相关项的状态"""
        if state == "normal":
            self.file_menu.entryconfig("保存", state="normal")
            self.file_menu.entryconfig("另存为...", state="normal")
        else:
            self.file_menu.entryconfig("保存", state="disabled")
            self.file_menu.entryconfig("另存为...", state="disabled")
    
    def open_config(self):
        """打开配置文件"""
        # 定义项目配置目录
        project_config_dir = project_root / "config" / "projects"
        if not project_config_dir.exists():
            project_config_dir = project_root / "config"
        
        file_path = filedialog.askopenfilename(
            title="选择项目配置文件",
            initialdir=project_config_dir,
            filetypes=[("INI Files", "*.ini"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                # 清空当前 notebook 内容
                for tab in self.notebook.tabs():
                    self.notebook.forget(tab)
                
                # 读取配置文件
                self.config.read(file_path, encoding='utf-8')
                self.current_file_path = file_path
                
                # 为每个 section 创建标签页
                for section in self.config.sections():
                    self.create_section_tab(section)
                
                # 更新菜单和状态栏
                self.update_menu_state("normal")
                self.status_var.set(f"已加载配置: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("错误", f"无法加载配置文件: {str(e)}")
                self.status_var.set("加载配置文件失败")

    def create_section_tab(self, section_name):
        """为配置文件的一个 section 创建标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=section_name)
        
        # 创建一个 Canvas 和 Scrollbar 来支持滚动
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 存储此标签页的控件引用
        section_widgets = {}
        
        # 为每个 option 创建控件
        for option in self.config.options(section_name):
            value = self.config.get(section_name, option)
            
            row_frame = ttk.Frame(scrollable_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # 创建标签
            label = ttk.Label(row_frame, text=option, width=25, anchor=tk.W)
            label.pack(side=tk.LEFT, padx=(0, 5))
            
            # 创建输入控件
            # 这里简化处理，都用 Entry，实际可以根据内容类型优化
            entry = ttk.Entry(row_frame, width=50)
            entry.insert(0, value)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            section_widgets[option] = entry
        
        # 将控件引用保存到 frame 的属性中
        frame.widgets = section_widgets
        frame.section_name = section_name

    def save_config(self):
        """保存配置文件"""
        if self.current_file_path:
            self._save_to_file(self.current_file_path)
    
    def save_config_as(self):
        """另存为配置文件"""
        if not self.current_file_path:
            return
            
        file_path = filedialog.asksaveasfilename(
            title="另存为项目配置文件",
            initialdir=os.path.dirname(self.current_file_path),
            defaultextension=".ini",
            filetypes=[("INI Files", "*.ini"), ("All Files", "*.*")]
        )
        
        if file_path:
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path):
        """将配置保存到指定文件"""
        try:
            # 遍历所有标签页，更新 config 对象
            for tab_id in range(self.notebook.index("end")):
                tab_frame = self.notebook.nametowidget(self.notebook.tabs()[tab_id])
                section_name = tab_frame.section_name
                widgets = tab_frame.widgets
                
                for option, entry_widget in widgets.items():
                    new_value = entry_widget.get()
                    self.config.set(section_name, option, new_value)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            
            self.current_file_path = file_path
            self.status_var.set(f"配置已保存: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", f"配置已保存到: {file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"无法保存配置文件: {str(e)}")
            self.status_var.set("保存配置文件失败")

    def show_about(self):
        """显示关于信息"""
        about_text = (
            "诗歌标注工具 - 项目配置编辑器\n\n"
            "版本: 1.0.0\n"
            "本工具用于简化编辑 poetry-annotator 项目的 .ini 配置文件。"
        )
        messagebox.showinfo("关于", about_text)
    
    def on_closing(self):
        """关闭窗口时的回调"""
        # 这里可以添加退出确认逻辑
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ProjectConfigEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()