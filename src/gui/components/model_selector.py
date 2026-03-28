"""模型选择器组件"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any, List


class ModelSelector(ttk.Frame):
    """
    可复用的模型选择组件
    
    提供模型名称下拉选择，支持单选/全选模式切换。
    """
    
    def __init__(
        self,
        master: Any,
        config_manager: Any,
        on_change: Optional[Callable] = None,
        label_text: str = "模型选择",
        show_all_option: bool = True
    ):
        """
        初始化模型选择器
        
        Args:
            master: 父容器
            config_manager: 配置管理器实例
            on_change: 选择变化时的回调函数
            label_text: 分组框标签文本
            show_all_option: 是否显示"全部模型"选项
        """
        super().__init__(master)
        self.config_manager = config_manager
        self.on_change = on_change
        self.show_all_option = show_all_option
        
        self.selected_model = tk.StringVar()
        self.model_choice_mode = tk.StringVar(value="single")  # "single" 或 "all"
        self._models: List[str] = []
        
        self._create_widgets(label_text)
        self._populate_models()
    
    def _create_widgets(self, label_text: str) -> None:
        """创建组件内的 widgets"""
        frame = ttk.LabelFrame(self, text=label_text)
        frame.pack(fill="x", padx=5, pady=5)
        
        # 单选模式
        self.single_radio = ttk.Radiobutton(
            frame,
            text="指定单个模型",
            variable=self.model_choice_mode,
            value="single",
            command=self._on_mode_change
        )
        self.single_radio.pack(side="left", padx=5, pady=5)
        
        # 模型下拉框
        self.combobox = ttk.Combobox(
            frame,
            textvariable=self.selected_model,
            state="readonly",
            width=30
        )
        self.combobox.pack(side="left", padx=5, pady=5)
        self.combobox.bind("<<ComboboxSelected>>", self._on_selection_change)
        
        # 全选模式（可选）
        if self.show_all_option:
            self.all_radio = ttk.Radiobutton(
                frame,
                text="使用所有已配置的模型",
                variable=self.model_choice_mode,
                value="all",
                command=self._on_mode_change
            )
            self.all_radio.pack(side="left", padx=20, pady=5)
    
    def _populate_models(self) -> None:
        """填充模型列表"""
        try:
            models = self.config_manager.list_model_configs()
            if models:
                self._models = models
                self.combobox['values'] = models
                self.combobox.set(models[0])
            else:
                self.combobox.set("无可用模型")
                self._models = []
        except Exception as e:
            self.combobox.set("加载失败")
            print(f"错误：加载模型配置失败：{e}")
    
    def _on_mode_change(self) -> None:
        """处理模式切换"""
        if self.on_change:
            self.on_change(self.get_selected_model(), self.is_all_models())
    
    def _on_selection_change(self, event: Optional[tk.Event] = None) -> None:
        """处理选择变化"""
        if self.on_change:
            self.on_change(self.get_selected_model(), self.is_all_models())
    
    def get_selected_model(self) -> str:
        """获取选中的模型名称"""
        return self.selected_model.get()
    
    def is_all_models(self) -> bool:
        """是否选择了全部模型"""
        return self.model_choice_mode.get() == "all"
    
    def set_enabled(self, enabled: bool) -> None:
        """设置组件启用状态"""
        state = "normal" if enabled else "disabled"
        
        # 单选模式时下拉框可用
        is_single_mode = self.model_choice_mode.get() == "single"
        self.single_radio['state'] = state
        self.combobox['state'] = 'readonly' if (enabled and is_single_mode) else 'disabled'
        
        if self.show_all_option:
            self.all_radio['state'] = state
    
    def update_state(self, is_running: bool = False) -> None:
        """根据任务运行状态更新 UI"""
        if is_running:
            self.set_enabled(False)
        else:
            self.set_enabled(True)
            # 根据当前模式更新下拉框状态
            is_single_mode = self.model_choice_mode.get() == "single"
            self.combobox['state'] = 'readonly' if is_single_mode else 'disabled'
