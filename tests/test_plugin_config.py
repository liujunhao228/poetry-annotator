"""
插件配置功能测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config_manager
from src.config.schema import GlobalPluginConfig, PluginConfig


def test_plugin_config():
    """测试插件配置加载功能"""
    print("测试插件配置加载功能...")
    
    # 获取全局插件配置
    global_plugin_config = config_manager.get_global_plugin_config()
    print(f"全局插件配置: {global_plugin_config}")
    
    # 验证配置类型
    assert isinstance(global_plugin_config, GlobalPluginConfig), "全局插件配置类型错误"
    
    # 获取特定插件配置
    plugin_config = config_manager.get_plugin_config("custom_query")
    print(f"自定义查询插件配置: {plugin_config}")
    
    # 验证配置类型
    assert isinstance(plugin_config, PluginConfig), "插件配置类型错误"
    
    # 验证插件是否启用
    assert plugin_config.enabled == True, "插件未启用"
    
    # 验证插件配置项
    assert "db_path" in plugin_config.settings, "缺少db_path配置项"
    print(f"插件数据库路径: {plugin_config.settings['db_path']}")
    
    print("所有测试通过!")


if __name__ == "__main__":
    test_plugin_config()