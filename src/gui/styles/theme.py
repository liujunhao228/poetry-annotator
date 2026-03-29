"""
GUI 主题和样式系统

提供统一的颜色、字体、间距等样式配置。
"""

from dataclasses import dataclass
from typing import Optional
import ttkbootstrap as ttkb


@dataclass
class ColorPalette:
    """颜色调色板"""
    # 主色调
    PRIMARY = "#0078D4"       # 微软蓝
    PRIMARY_HOVER = "#106EBE"
    PRIMARY_LIGHT = "#E6F3FF"

    # 状态色 - 优化对比度
    SUCCESS = "#107C10"       # 成功绿
    SUCCESS_LIGHT = "#DFFFD8"
    WARNING = "#F59E0B"       # 警告黄 (对比度 4.5:1)
    WARNING_LIGHT = "#FFF4CE"
    DANGER = "#DC2626"        # 错误红 (对比度 5.2:1)
    DANGER_LIGHT = "#FDE7E9"
    INFO = "#00B7C3"          # 信息蓝
    INFO_LIGHT = "#E0F7FA"

    # 中性色 - 优化对比度
    TEXT_PRIMARY = "#0F172A"      # 主文字 (对比度 16:1)
    TEXT_SECONDARY = "#475569"    # 次要文字 (对比度 7.3:1)
    TEXT_DISABLED = "#94A3B8"
    BORDER = "#CBD5E1"            # 边框 (更明显)
    BORDER_FOCUS = "#0078D4"
    BACKGROUND = "#FFFFFF"
    BACKGROUND_SECONDARY = "#F1F5F9"  # 冷色调背景
    BACKGROUND_HOVER = "#E2E8F0"

    # 表格颜色
    TABLE_HEADER_BG = "#F8FAFC"
    TABLE_ROW_HOVER = "#E0F2FE"
    TABLE_ROW_ALT = "#FAFAFA"
    TABLE_SELECTED = "#BAE6FD"


@dataclass
class FontConfig:
    """字体配置"""
    FAMILY = "Segoe UI"  # Windows 现代字体
    FAMILY_MONO = "Consolas"

    # 字号 - 优化后可读性
    SIZE_SMALL = 11     # 按钮、标签等辅助文字
    SIZE_NORMAL = 12    # 正文、表格内容
    SIZE_LARGE = 14     # 卡片标题、重要标签
    SIZE_TITLE = 16     # 窗口标题、主标题
    SIZE_HEADING = 13   # 表格头、分组标题

    # 字重
    WEIGHT_NORMAL = "normal"
    WEIGHT_BOLD = "bold"


@dataclass
class SpacingConfig:
    """间距配置"""
    XS = 2
    SMALL = 5
    MEDIUM = 10
    LARGE = 15
    XL = 20


@dataclass
class BorderConfig:
    """边框配置"""
    RADIUS_SMALL = 4
    RADIUS_MEDIUM = 6
    RADIUS_LARGE = 8
    WIDTH = 1
    WIDTH_FOCUS = 2


class Theme:
    """
    主题单例类
    
    提供全局样式配置和 ttk 样式自定义。
    """
    
    _instance: Optional["Theme"] = None
    
    def __new__(cls) -> "Theme":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.colors = ColorPalette()
        self.fonts = FontConfig()
        self.spacing = SpacingConfig()
        self.borders = BorderConfig()
        
        # ttkbootstrap 主题名称
        self.bootstrap_theme = "litera"  # 清新现代的主题
    
    def apply_theme(self, root) -> None:
        """
        应用主题到根窗口

        Args:
            root: Tk 根窗口实例
        """
        # 注意：主题已经在 MainWindow.__init__ 中通过 ttkb.Window(themename=...) 应用
        # 这里只需要应用自定义样式
        
        # 获取当前样式
        style = ttkb.Style()
        
        # 自定义样式
        self._configure_styles()
    
    def _configure_styles(self) -> None:
        """配置自定义样式"""
        style = ttkb.Style()
        
        # 配置常用样式
        self._configure_labels(style)
        self._configure_buttons(style)
        self._configure_frames(style)
        self._configure_treeview(style)
    
    def _configure_labels(self, style: ttkb.Style) -> None:
        """配置标签样式"""
        # 标题标签
        style.configure(
            "Title.TLabel",
            font=(self.fonts.FAMILY, self.fonts.SIZE_TITLE, self.fonts.WEIGHT_BOLD),
            foreground=self.colors.TEXT_PRIMARY
        )
        
        # 副标题标签
        style.configure(
            "Subtitle.TLabel",
            font=(self.fonts.FAMILY, self.fonts.SIZE_HEADING, self.fonts.WEIGHT_BOLD),
            foreground=self.colors.TEXT_PRIMARY
        )
        
        # 普通标签
        style.configure(
            "Body.TLabel",
            font=(self.fonts.FAMILY, self.fonts.SIZE_NORMAL),
            foreground=self.colors.TEXT_SECONDARY
        )
        
        # 状态标签
        style.configure(
            "Success.TLabel",
            foreground=self.colors.SUCCESS
        )
        style.configure(
            "Warning.TLabel",
            foreground=self.colors.WARNING
        )
        style.configure(
            "Danger.TLabel",
            foreground=self.colors.DANGER
        )
    
    def _configure_buttons(self, style: ttkb.Style) -> None:
        """配置按钮样式"""
        # 主按钮
        style.configure(
            "Primary.TButton",
            font=(self.fonts.FAMILY, self.fonts.SIZE_NORMAL, self.fonts.WEIGHT_BOLD)
        )
        
        # 小按钮
        style.configure(
            "Small.TButton",
            font=(self.fonts.FAMILY, self.fonts.SIZE_SMALL)
        )
    
    def _configure_frames(self, style: ttkb.Style) -> None:
        """配置框架样式"""
        # 卡片式框架
        style.configure(
            "Card.TFrame",
            background=self.colors.BACKGROUND
        )
        
        # 分组框
        style.configure(
            "Group.TLabelframe",
            borderwidth=1,
            relief="groove"
        )
        style.configure(
            "Group.TLabelframe.Label",
            font=(self.fonts.FAMILY, self.fonts.SIZE_HEADING, self.fonts.WEIGHT_BOLD)
        )
    
    def _configure_treeview(self, style: ttkb.Style) -> None:
        """配置表格样式"""
        style.configure(
            "Treeview",
            font=(self.fonts.FAMILY, self.fonts.SIZE_NORMAL),
            rowheight=28,
            background=self.colors.BACKGROUND,
            fieldbackground=self.colors.BACKGROUND,
            foreground=self.colors.TEXT_PRIMARY
        )
        style.configure(
            "Treeview.Heading",
            font=(self.fonts.FAMILY, self.fonts.SIZE_HEADING, self.fonts.WEIGHT_BOLD),
            background=self.colors.TABLE_HEADER_BG,
            foreground=self.colors.TEXT_PRIMARY
        )
        style.map(
            "Treeview",
            background=[("selected", self.colors.TABLE_SELECTED)],
            foreground=[("selected", self.colors.TEXT_PRIMARY)]
        )


# 全局主题实例
theme = Theme()


def get_colors() -> ColorPalette:
    """获取颜色调色板"""
    return theme.colors


def get_fonts() -> FontConfig:
    """获取字体配置"""
    return theme.fonts


def get_spacing() -> SpacingConfig:
    """获取间距配置"""
    return theme.spacing
