"""
插件使用示例
"""
from src.data import plugin_manager
from src.data.models import Poem, Author, create_model_instance, serialize_model, get_model_fields


def main():
    # 通过插件管理器创建模型实例
    poem_data = {
        "id": 1,
        "title": "静夜思",
        "author": "李白",
        "paragraphs": ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"],
        "full_text": "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
    }
    
    # 方法1: 使用create_model_instance函数
    poem = create_model_instance("Poem", poem_data)
    print(f"创建的诗词: {poem.title} - {poem.author}")
    
    # 方法2: 使用模型别名函数
    author_data = {
        "name": "李白",
        "description": "唐代伟大诗人"
    }
    author = Author(author_data)
    print(f"创建的作者: {author.name}")
    
    # 序列化模型实例
    serialized_poem = serialize_model(poem)
    print(f"序列化的诗词: {serialized_poem}")
    
    # 获取模型字段
    fields = get_model_fields("Poem")
    print(f"Poem模型字段: {fields}")


if __name__ == "__main__":
    main()