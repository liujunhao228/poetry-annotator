"""
插件化标签解析器
完全由插件提供情感分类信息
"""

import logging
from collections import OrderedDict
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.data.label_parser_plugin_interface import LabelParserPlugin
from src.config.schema import PluginConfig
from src.data.plugin_interface import QueryPluginManager
from src.component_system import Component, ComponentType, get_component_system

# 全局插件化标签解析器实例
_plugin_label_parser_instance: Optional['PluginBasedLabelParser'] = None


class PluginBasedLabelParser(Component):
    """基于插件的标签解析器，完全依赖插件提供情感分类"""
    
    def __init__(self, config_manager=None):
        """
        初始化插件化标签解析器
        
        Args:
            config_manager: 配置管理器实例
        """
        # 调用父类构造函数，设置组件类型
        super().__init__(ComponentType.LABEL_PARSER)
        
        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 存储配置管理器
        self.config_manager = config_manager
        
        # 初始化插件系统
        self._initialize_plugins()
        
        # 存储从插件获取的分类信息
        self.categories = OrderedDict()
        self._load_categories_from_plugins()
    
    def _initialize_plugins(self):
        """初始化插件系统"""
        try:
            if not self.config_manager:
                # 延迟导入配置管理器以避免循环依赖
                try:
                    from .config import config_manager
                    self.config_manager = config_manager
                except ImportError:
                    # 当作为独立模块运行时
                    import sys
                    from pathlib import Path
                    sys.path.append(str(Path(__file__).parent))
                    from config import config_manager
                    self.config_manager = config_manager
            
            # 创建插件管理器实例
            self.plugin_manager = QueryPluginManager(self.config_manager)
            
            # 加载插件
            self.plugin_manager.load_plugins_from_config()
            
            self.logger.info("插件系统初始化完成")
        except Exception as e:
            self.logger.warning(f"插件系统初始化失败: {e}")
            self.plugin_manager = None
    
    def _load_categories_from_plugins(self):
        """从插件加载情感分类体系"""
        if not self.plugin_manager:
            self.logger.warning("插件管理器未初始化，无法加载分类信息")
            return
        
        # 获取所有标签解析插件
        label_parser_plugins = self._get_label_parser_plugins()
        
        # 合并所有插件提供的分类信息
        for plugin_name, plugin in label_parser_plugins.items():
            try:
                plugin_categories = plugin.get_categories()
                if plugin_categories:
                    # 合并插件分类信息
                    for category_id, category_data in plugin_categories.items():
                        if category_id not in self.categories:
                            self.categories[category_id] = category_data
                        else:
                            # 合并现有分类和插件分类信息
                            self.categories[category_id].update(category_data)
                    
                    self.logger.info(f"从插件 '{plugin_name}' 加载了 {len(plugin_categories)} 个分类")
                else:
                    self.logger.warning(f"插件 '{plugin_name}' 未提供任何分类信息")
            except Exception as e:
                self.logger.warning(f"从插件 '{plugin_name}' 加载分类信息时出错: {e}")
    
    def _get_label_parser_plugins(self) -> Dict[str, LabelParserPlugin]:
        """获取所有标签解析插件"""
        label_parser_plugins = {}
        
        if not self.plugin_manager:
            return label_parser_plugins
        
        # 获取所有插件
        all_plugins = self.plugin_manager.plugins
        
        # 筛选出标签解析插件（继承自LabelParserPlugin的插件）
        for plugin_name, plugin in all_plugins.items():
            if isinstance(plugin, LabelParserPlugin):
                label_parser_plugins[plugin_name] = plugin
        
        return label_parser_plugins
    
    def get_categories_text(self) -> str:
        """获取格式化的情感分类文本，用于提示词"""
        text = "## 情感分类体系：\n\n"
        
        for category_id, category_data in self.categories.items():
            text += f"**{category_id}. {category_data.get('name_zh', '')}** ({category_data.get('name_en', '')})\n"
            # 使用'categories'而不是'secondaries'
            for secondary in category_data.get('categories', []):
                text += f"- **{secondary.get('id', '')} {secondary.get('name_zh', '')}** ({secondary.get('name_en', '')})\n"
            text += "\n"
        
        return text
    
    def get_all_categories(self) -> List[str]:
        """获取所有情感分类名称"""
        categories = []
        for category_data in self.categories.values():
            categories.append(category_data.get('name_zh', ''))
            # 使用'categories'而不是'secondaries'
            categories.extend([sec.get('name_zh', '') for sec in category_data.get('categories', [])])
        return categories
    
    def get_all_categories_with_ids(self) -> Dict[str, str]:
        """获取所有情感分类ID和名称的映射"""
        categories = {}
        for category_id, category_data in self.categories.items():
            categories[category_id] = category_data.get('name_zh', '')
            # 使用'categories'而不是'secondaries'
            for secondary in category_data.get('categories', []):
                categories[secondary.get('id', '')] = secondary.get('name_zh', '')
        return categories
    
    def validate_emotion(self, emotion: str) -> bool:
        """验证情感标签是否在分类体系中"""
        all_categories = self.get_all_categories()
        return emotion in all_categories
    
    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """根据二级类别ID获取一级类别ID"""
        # 使用'categories'而不是'secondaries'
        for category_id, category_data in self.categories.items():
            for secondary in category_data.get('categories', []):
                if secondary.get('id', '') == secondary_id:
                    return category_id
        return None
    
    def execute_plugin_method(self, plugin_name: str, method_name: str, *args, **kwargs) -> Any:
        """
        执行插件方法
        
        Args:
            plugin_name: 插件名称
            method_name: 要执行的方法名
            *args: 方法参数
            **kwargs: 方法关键字参数
            
        Returns:
            方法执行结果
            
        Raises:
            Exception: 插件或方法执行错误
        """
        if not self.plugin_manager:
            raise Exception("插件系统未初始化")
        
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            raise Exception(f"未找到插件: {plugin_name}")
        
        if not hasattr(plugin, method_name):
            raise Exception(f"插件 {plugin_name} 不存在方法: {method_name}")
        
        method = getattr(plugin, method_name)
        return method(*args, **kwargs)


# 全局标签解析器实例获取函数
def get_plugin_label_parser(project_root=None, config_manager=None):
    """获取全局插件化标签解析器实例（通过组件系统）"""
    # 如果提供了项目根目录，则使用组件系统获取实例
    if project_root:
        component_system = get_component_system(project_root)
        return component_system.get_component(ComponentType.LABEL_PARSER, config_manager=config_manager)
    
    # 否则使用原来的单例模式
    global _plugin_label_parser_instance
    if _plugin_label_parser_instance is None:
        _plugin_label_parser_instance = PluginBasedLabelParser(config_manager)
    return _plugin_label_parser_instance