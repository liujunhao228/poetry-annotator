# 数据模型插件系统

## 概述

本项目采用插件化架构管理数据模型定义，以提高代码的模块化和可维护性。

## 文件结构

- `models_combined.py`: 包含所有数据模型的定义（dataclass形式）
- `model_plugin_interface.py`: 插件接口定义
- `model_definition_plugin.py`: 数据模型定义插件的具体实现
- `model_plugin_loader.py`: 插件加载器
- `model_plugin_example.py`: 使用示例

## 使用方法

### 基本用法

```python
from src.data.model_plugin_loader import model_plugin_manager

# 获取模型类
poem_class = manager.get_model_class("data_model_definition", "Poem")

# 创建模型实例
poem_data = {
    "id": 1,
    "title": "示例诗",
    "author": "示例作者",
    "paragraphs": ["第一段", "第二段"],
    "full_text": "完整文本"
}

poem_instance = manager.create_model_instance("data_model_definition", "Poem", poem_data)

# 获取模型字段
poem_fields = manager.get_model_fields("data_model_definition", "Poem")
```

### 向后兼容

为了保持向后兼容性，原有的模型导入方式仍然有效：

```python
from src.data.models import Poem, Author
from src.data.models_sentence_strategy_link import SentenceStrategyLink
```

## 扩展插件

要创建新的模型定义插件：

1. 继承 `ModelDefinitionPlugin` 抽象基类
2. 实现必要的方法
3. 在 `model_plugin_loader.py` 中注册插件

## 注意事项

- SQLAlchemy模型部分已移除，数据库操作应通过其他方式实现
- 插件系统主要管理数据模型的定义和实例化