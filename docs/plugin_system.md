# 插件系统文档

## 1. 概述

插件系统是诗词标注项目的核心组件之一，它提供了一种灵活的方式来扩展系统功能，而无需修改核心代码。通过插件系统，开发者可以轻松地添加新的功能模块，如数据查询、预处理、Prompt构建等。

## 2. 插件类型

插件系统支持以下几种类型的插件：

1. **查询插件 (QueryPlugin)**: 用于执行数据查询操作
2. **预处理插件 (PreprocessingPlugin)**: 用于数据预处理操作
3. **Prompt构建插件 (PromptBuilderPlugin)**: 用于构建LLM提示词
4. **标签解析插件 (LabelParserPlugin)**: 用于解析和扩展标签分类
5. **数据库初始化插件 (DatabaseInitPlugin)**: 用于数据库初始化操作

## 3. 插件接口

### 3.1 基础插件接口

所有插件都必须继承 `BasePlugin` 类并实现以下方法：

```python
class BasePlugin(ABC):
    def __init__(self, plugin_config: PluginConfig):
        self.plugin_config = plugin_config
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    def initialize(self) -> bool:
        """初始化插件"""
        return True
    
    def cleanup(self) -> bool:
        """清理插件资源"""
        return True
```

### 3.2 特定类型插件接口

#### 查询插件
```python
class QueryPlugin(BasePlugin):
    @abstractmethod
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行查询操作"""
        pass
    
    @abstractmethod
    def get_required_params(self) -> List[str]:
        """获取必需参数列表"""
        pass
```

#### 预处理插件
```python
class PreprocessingPlugin(BasePlugin):
    @abstractmethod
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行预处理操作"""
        pass
```

## 4. 插件管理器

插件管理器 (`PluginManager`) 负责插件的注册、获取、初始化和清理。

### 4.1 主要方法

- `register_plugin(plugin: BasePlugin) -> bool`: 注册插件
- `unregister_plugin(plugin_name: str) -> bool`: 注销插件
- `get_plugin(plugin_name: str) -> Optional[BasePlugin]`: 获取插件实例
- `list_plugins() -> Dict[str, str]`: 列出所有插件
- `initialize_all_plugins() -> Dict[str, bool]`: 初始化所有插件
- `cleanup_all_plugins() -> Dict[str, bool]`: 清理所有插件资源

## 5. 插件配置

插件通过配置文件进行管理，配置文件采用INI格式：

```ini
[GlobalPlugins]
enabled_plugins = plugin1,plugin2
plugin_paths = project/plugins

[Plugin.plugin1]
enabled = true
type = query
module = src.data.plugins.custom_query
class = CustomQueryPlugin
description = 自定义查询插件
```

## 6. 插件开发指南

### 6.1 创建新插件

1. 选择合适的插件类型基类
2. 实现所有抽象方法
3. 在配置文件中添加插件配置
4. 测试插件功能

### 6.2 示例插件实现

```python
from src.plugin_system.interfaces import QueryPlugin
from src.config.schema import PluginConfig

class CustomQueryPlugin(QueryPlugin):
    def get_name(self) -> str:
        return "custom_query"
    
    def get_description(self) -> str:
        return "自定义查询插件"
    
    def execute_query(self, params=None):
        # 实现查询逻辑
        import pandas as pd
        return pd.DataFrame()
    
    def get_required_params(self) -> list:
        return ["table_name"]
```

## 7. 插件适配器

为了保持向后兼容，系统提供了插件适配器，可以将旧的插件实现适配到新的插件系统。

## 8. 最佳实践

1. **插件命名**: 使用清晰、描述性的名称
2. **错误处理**: 在插件中实现适当的错误处理
3. **资源管理**: 正确实现初始化和清理方法
4. **配置管理**: 合理使用插件配置
5. **日志记录**: 添加适当的日志记录