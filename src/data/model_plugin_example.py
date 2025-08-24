"""
模型插件使用示例
"""
from src.data.model_plugin_loader import model_plugin_manager


def example_usage():
    """使用示例"""
    # 获取插件管理器
    manager = model_plugin_manager
    
    # 列出所有插件
    print("可用插件:")
    for name, description in manager.list_plugins().items():
        print(f"  {name}: {description}")
    
    # 获取模型类
    poem_class = manager.get_model_class("data_model_definition", "Poem")
    if poem_class:
        print(f"\n成功获取Poem模型类: {poem_class}")
    
    # 创建模型实例
    poem_data = {
        "id": 1,
        "title": "示例诗",
        "author": "示例作者",
        "paragraphs": ["第一段", "第二段"],
        "full_text": "完整文本",
        "author_desc": "作者描述"
    }
    
    poem_instance = manager.create_model_instance("data_model_definition", "Poem", poem_data)
    if poem_instance:
        print(f"\n成功创建Poem实例: {poem_instance}")
        print(f"Poem实例的标题: {poem_instance.title}")
    
    # 获取模型字段
    poem_fields = manager.get_model_fields("data_model_definition", "Poem")
    if poem_fields:
        print(f"\nPoem模型字段: {poem_fields}")


if __name__ == "__main__":
    example_usage()