"""
插件化查询使用示例
"""

from src.data.enhanced_manager import EnhancedDataManager
from src.data.plugins.custom_query_plugin import CustomQueryPlugin


def main():
    # 初始化数据管理器
    db_path = "data/poetry.db"  # 替换为实际的数据库路径
    data_manager = EnhancedDataManager(db_path)
    
    # 注册自定义插件
    try:
        custom_plugin = CustomQueryPlugin()
        data_manager.plugin_query_manager.register_plugin(custom_plugin)
        
        # 列出所有插件
        print("可用插件:")
        plugins = data_manager.list_plugins()
        for name, description in plugins.items():
            print(f"- {name}: {description}")
        
        # 执行自定义查询 - 原始数据
        print("\n自定义查询结果 (原始数据):")
        custom_df = data_manager.execute_plugin_query("custom_query", {"type": "poem"})
        print(custom_df.head())
        
        # 执行自定义查询 - 标注数据
        print("\n自定义查询结果 (标注数据):")
        custom_df = data_manager.execute_plugin_query("custom_query", {"type": "annotation"})
        print(custom_df.head())
        
        # 执行自定义查询 - 情感分类数据
        print("\n自定义查询结果 (情感分类数据):")
        custom_df = data_manager.execute_plugin_query("custom_query", {"type": "emotion"})
        print(custom_df.head())
        
    except Exception as e:
        print(f"插件查询示例运行出错: {e}")
        print("这可能是因为数据库文件不存在或其他配置问题")


if __name__ == "__main__":
    main()