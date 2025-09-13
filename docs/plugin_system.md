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
6. **响应验证器插件 (ResponseValidatorPlugin)**: 用于验证LLM响应结果
7. **LLM服务插件 (LLMServicePlugin)**: 用于提供LLM服务功能，包括模拟服务

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

#### 响应验证器插件
```python
class ResponseValidatorPlugin(BasePlugin):
    @abstractmethod
    def validate(self, result_list: list) -> List[Dict[str, Any]]:
        """
        验证标注列表的内容。
        Args:
            result_list: 解析后的标注列表。
        Returns:
            一个经过验证的、包含标注信息的字典列表。
        Raises:
            ValueError, TypeError: 如果验证失败。
        """
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

插件通过配置文件 `project/plugins.ini` 进行管理，该文件采用INI格式。系统会自动加载所有 `enabled = true` 的插件。

每个插件都在一个独立的 `[Plugin.插件名称]` 部分中进行配置。

```ini
[Plugin.plugin1]
enabled = true
path = src/data/plugins
type = query
module = custom_query
class = CustomQueryPlugin
```

### 配置项说明

- `enabled`: (必需) `true` 或 `false`，决定是否加载此插件。
- `path`: (必需) 插件源代码所在的根目录路径（相对于项目根目录）。加载器会自动将此路径添加到 `sys.path`。
- `type`: (必需) 插件的类型，必须是 `ComponentType` 枚举中定义的值之一（例如 `query`, `preprocessing`, `response_validator` 等）。
- `module`: (必需) 包含插件类的Python模块路径。
- `class`: (必需) 插件的主类名。
- 其他自定义字段：插件可以包含任意数量的自定义配置项，这些配置项会作为 `settings` 字典传递给插件的构造函数。

### 示例：同时启用多个插件

```ini
# 默认响应验证插件
[Plugin.default_response_validation]
enabled = true
path = src/response_validation
type = response_validator
module = src.response_validation.plugin_impl
class = DefaultResponseValidationPlugin

# 自定义查询插件
[Plugin.custom_query]
enabled = true
path = project/plugins/custom_query_plugin
type = query
module = custom_query_logic
class = CustomQueryPlugin
table_name = "poems" # 自定义配置项
```

## 6. 插件开发指南

### 6.1 创建新插件

1. 选择合适的插件类型基类
2. 实现所有抽象方法
3. 在配置文件中添加插件配置
4. 测试插件功能

### 6.2 示例插件实现

#### 查询插件示例
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

#### 响应验证器插件
```python
from src.plugin_system.interfaces import ResponseValidatorPlugin
from src.config.schema import PluginConfig

class CustomResponseValidatorPlugin(ResponseValidatorPlugin):
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(plugin_config)
        
    def get_name(self) -> str:
        return "custom_response_validator"
    
    def get_description(self) -> str:
        return "自定义响应验证器插件"
    
    def validate(self, result_list: list) -> List[Dict[str, Any]]:
        # 实现自定义验证逻辑
        if not result_list:
            raise ValueError("结果列表不能为空")
        
        # 添加自定义验证规则
        for i, item in enumerate(result_list):
            # 示例：检查ID是否为数字字符串
            if 'id' in item and not item['id'].isdigit():
                raise ValueError(f"第{i+1}项的ID必须是数字字符串")
                
        return result_list
```

#### LLM服务插件
```python
from src.plugin_system.interfaces import LLMServicePlugin
from src.config.schema import PluginConfig
from src.llm_services.schemas import PoemData, EmotionSchema

class CustomLLMServicePlugin(LLMServicePlugin):
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(plugin_config)
        
    def get_name(self) -> str:
        return "custom_llm_service"
    
    def get_description(self) -> str:
        return "自定义LLM服务插件"
    
    async def annotate_poem(self, poem: PoemData, emotion_schema: EmotionSchema) -> List[Dict[str, Any]]:
        # 实现诗词标注逻辑
        pass
    
    async def annotate_poem_stream(self, poem: PoemData, emotion_schema: EmotionSchema) -> str:
        # 实现流式诗词标注逻辑
        pass
    
    async def health_check(self) -> Tuple[bool, str]:
        # 实现健康检查逻辑
        return True, "Service is healthy"
```

## 7. 最佳实践

1. **插件命名**: 使用清晰、描述性的名称
2. **错误处理**: 在插件中实现适当的错误处理
3. **资源管理**: 正确实现初始化和清理方法
4. **配置管理**: 合理使用插件配置
5. **日志记录**: 添加适当的日志记录