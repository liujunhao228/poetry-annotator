"""
模型插件加载器
"""
from src.data.model_plugin_interface import ModelDefinitionPluginManager
from src.data.model_definition_plugin import DataModelDefinitionPlugin


def load_model_plugins() -> ModelDefinitionPluginManager:
    """加载模型插件"""
    manager = ModelDefinitionPluginManager()
    
    # 注册数据模型定义插件
    data_model_plugin = DataModelDefinitionPlugin()
    manager.register_plugin(data_model_plugin)
    
    return manager


# 全局插件管理器实例
model_plugin_manager = load_model_plugins()