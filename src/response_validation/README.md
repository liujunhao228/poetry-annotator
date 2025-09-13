# 响应验证模块

## 概述

响应验证模块提供了一套完整的框架用于处理响应验证功能。该模块采用了插件化架构，支持自定义响应验证插件。

## 模块结构

- `interface.py`: 定义响应验证插件接口
- `core.py`: 核心处理器，负责协调插件调用
- `manager.py`: 管理器类，提供统一的API接口
- `plugin_adapter.py`: 插件适配器，用于与组件系统集成
- `default_plugin.py`: 默认插件实现
- `example_plugin.py`: 示例插件实现

## 使用方法

### 1. 使用管理器类（推荐）

```python
from src.response_validation import ResponseValidationManager

# 创建管理器实例
manager = ResponseValidationManager()

# 验证响应
result = manager.validate_response(解析后的标注列表)
```

### 2. 使用核心类

```python
from src.response_validation import ResponseValidationCore

# 创建核心处理器实例
core = ResponseValidationCore()

# 验证响应
result = core.validate_response(解析后的标注列表)
```

## 插件开发

要开发自定义响应验证插件，需要：

1. 继承 `ResponseValidationPlugin` 接口
2. 实现所有抽象方法
3. 在项目配置中注册插件

示例插件请参考 `example_plugin.py` 文件。