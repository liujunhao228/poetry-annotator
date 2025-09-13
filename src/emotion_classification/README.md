# 情感分类模块

## 概述

情感分类模块提供了一套完整的框架用于处理诗词情感分类功能。该模块采用了插件化架构，支持自定义情感分类插件。

## 模块结构

- `interface.py`: 定义情感分类插件接口
- `core.py`: 核心处理器，负责协调插件调用
- `manager.py`: 管理器类，提供统一的API接口
- `plugin_adapter.py`: 插件适配器，用于与组件系统集成
- `example_plugin.py`: 示例插件实现

## 使用方法

### 1. 使用管理器类（推荐）

```python
from src.emotion_classification import EmotionClassificationManager

# 创建管理器实例
manager = EmotionClassificationManager()

# 获取情感显示信息
info = manager.get_emotion_display_info("01.05")
print(info)  # {'id': '01.05', 'name': '01.05 愉悦'}

# 获取完整情感列表
emotion_list = manager.get_full_emotion_list_for_selection()
```

### 2. 使用核心类

```python
from src.emotion_classification import EmotionClassificationCore

# 创建核心处理器实例
core = EmotionClassificationCore()

# 获取情感分类文本
text = core.get_categories_text()
print(text)
```

## 插件开发

要开发自定义情感分类插件，需要：

1. 继承 `EmotionClassificationPlugin` 接口
2. 实现所有抽象方法
3. 在项目配置中注册插件

示例插件请参考 `example_plugin.py` 文件。

## 向后兼容

为了保持向后兼容性，原有的 `EmotionClassifier` 类已被重构为适配器模式，内部使用新的情感分类模块。