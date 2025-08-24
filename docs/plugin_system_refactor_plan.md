# 插件系统重构方案

## 1. 目标

1. 统一所有插件实现的接口规范
2. 设计统一的插件管理器
3. 实现插件的动态加载和注册机制
4. 提供插件生命周期管理
5. 保持向后兼容性

## 2. 设计原则

1. **统一接口**：所有插件都必须实现统一的插件接口
2. **可扩展性**：支持不同类型的插件扩展
3. **松耦合**：插件与核心系统之间保持松耦合
4. **配置化**：通过配置文件管理插件的启用/禁用
5. **向后兼容**：支持现有插件的平滑迁移

## 3. 统一插件接口设计

### 3.1 基础插件接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.config.schema import PluginConfig

class BasePlugin(ABC):
    """基础插件接口"""
    
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
    
    def get_config(self) -> PluginConfig:
        """获取插件配置"""
        return self.plugin_config
```

### 3.2 特定类型插件接口

#### 3.2.1 数据查询插件接口

```python
from src.plugin_system.base import BasePlugin
import pandas as pd
from typing import Optional, Dict, Any

class QueryPlugin(BasePlugin):
    """数据查询插件接口"""
    
    @abstractmethod
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行查询操作"""
        pass
    
    @abstractmethod
    def get_required_params(self) -> list:
        """获取必需参数列表"""
        pass
```

#### 3.2.2 数据预处理插件接口

```python
from src.plugin_system.base import BasePlugin
from typing import Dict, Any

class PreprocessingPlugin(BasePlugin):
    """数据预处理插件接口"""
    
    @abstractmethod
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行预处理操作"""
        pass
```

#### 3.2.3 Prompt构建插件接口

```python
from src.plugin_system.base import BasePlugin
from typing import Tuple, Dict, Any
from src.llm_services.schemas import PoemData, EmotionSchema

class PromptBuilderPlugin(BasePlugin):
    """Prompt构建插件接口"""
    
    @abstractmethod
    def build_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema, 
                     model_config: Dict[str, Any]) -> Tuple[str, str]:
        """构建系统提示词和用户提示词"""
        pass
```

#### 3.2.4 标签解析插件接口

```python
from src.plugin_system.base import BasePlugin
from typing import Dict, Any

class LabelParserPlugin(BasePlugin):
    """标签解析插件接口"""
    
    @abstractmethod
    def get_categories(self) -> Dict[str, Any]:
        """获取插件提供的额外分类信息"""
        pass
    
    def extend_category_data(self, categories: Dict[str, Any]) -> Dict[str, Any]:
        """扩展分类数据"""
        extended = categories.copy()
        plugin_categories = self.get_categories()
        
        # 合并分类信息
        for category_id, category_data in plugin_categories.items():
            if category_id not in extended:
                extended[category_id] = category_data
            else:
                # 合并现有分类和插件分类信息
                extended[category_id].update(category_data)
        
        return extended
```

#### 3.2.5 数据库初始化插件接口

```python
from src.plugin_system.base import BasePlugin
from typing import Dict, Any

class DatabaseInitPlugin(BasePlugin):
    """数据库初始化插件接口"""
    
    @abstractmethod
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库"""
        pass
    
    def on_database_initialized(self, db_name: str, result: Dict[str, Any]):
        """数据库初始化完成后的回调方法"""
        pass
```

## 4. 统一插件管理器设计

### 4.1 插件管理器接口

```python
from typing import Dict, Any, Optional, List
from src.plugin_system.base import BasePlugin

class PluginManager:
    """统一插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Any] = {}
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """注册插件"""
        plugin_name = plugin.get_name()
        if plugin_name in self.plugins:
            return False
        self.plugins[plugin_name] = plugin
        return True
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        if plugin_name in self.plugins:
            # 先清理插件资源
            plugin = self.plugins[plugin_name]
            plugin.cleanup()
            del self.plugins[plugin_name]
            return True
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件"""
        return {name: plugin.get_description() for name, plugin in self.plugins.items()}
    
    def initialize_all_plugins(self) -> Dict[str, bool]:
        """初始化所有插件"""
        results = {}
        for name, plugin in self.plugins.items():
            try:
                results[name] = plugin.initialize()
            except Exception as e:
                results[name] = False
        return results
    
    def cleanup_all_plugins(self) -> Dict[str, bool]:
        """清理所有插件资源"""
        results = {}
        for name, plugin in self.plugins.items():
            try:
                results[name] = plugin.cleanup()
            except Exception as e:
                results[name] = False
        return results
```

### 4.2 插件加载器

```python
import importlib
from typing import Dict, Any
from src.plugin_system.base import BasePlugin
from src.plugin_system.manager import PluginManager
from src.config.schema import PluginConfig

class PluginLoader:
    """插件加载器"""
    
    @staticmethod
    def load_plugin(plugin_config: PluginConfig) -> BasePlugin:
        """根据配置加载插件"""
        module_name = plugin_config.module
        class_name = plugin_config.class_name
        
        # 动态导入模块
        module = importlib.import_module(module_name)
        plugin_class = getattr(module, class_name)
        
        # 创建插件实例
        plugin = plugin_class(plugin_config)
        return plugin
    
    @staticmethod
    def load_plugins_from_config(config_manager, plugin_manager: PluginManager):
        """根据配置管理器加载所有启用的插件"""
        # 获取全局插件配置
        global_plugin_config = config_manager.get_global_plugin_config()
        
        # 遍历启用的插件列表
        for plugin_name in global_plugin_config.enabled_plugins:
            try:
                # 获取插件配置
                plugin_config = config_manager.get_plugin_config(plugin_name)
                
                # 如果插件被禁用，跳过
                if not plugin_config.enabled:
                    continue
                
                # 加载插件
                plugin = PluginLoader.load_plugin(plugin_config)
                
                # 注册插件
                plugin_manager.register_plugin(plugin)
                
            except Exception as e:
                print(f"警告: 加载插件 '{plugin_name}' 时出错: {e}")
```

## 5. 插件配置管理

### 5.1 插件配置结构

```ini
[GlobalPlugins]
enabled_plugins = plugin1,plugin2,plugin3
plugin_paths = project/plugins

[Plugin.plugin1]
enabled = true
type = query
module = src.data.plugins.custom_query
class = CustomQueryPlugin
description = 自定义查询插件

[Plugin.plugin2]
enabled = true
type = preprocessing
module = src.data_cleaning.plugins.custom_cleaner
class = CustomCleanerPlugin
description = 自定义数据清洗插件
```

### 5.2 配置管理器增强

```python
class ConfigManager:
    """配置管理器增强版"""
    
    def get_global_plugin_config(self):
        """获取全局插件配置"""
        # 实现获取全局插件配置的逻辑
        pass
    
    def get_plugin_config(self, plugin_name: str) -> PluginConfig:
        """获取特定插件配置"""
        # 实现获取特定插件配置的逻辑
        pass
```

## 6. 迁移方案

### 6.1 现有插件适配

为现有插件创建适配器类，使其符合新的统一接口规范：

```python
# 示例：查询插件适配器
class QueryPluginAdapter(QueryPlugin):
    """查询插件适配器"""
    
    def __init__(self, plugin_config: PluginConfig):
        super().__init__(plugin_config)
        # 适配原有插件实现
        self.adaptee = self._load_legacy_plugin()
    
    def _load_legacy_plugin(self):
        """加载原有的插件实现"""
        # 实现加载逻辑
        pass
    
    def get_name(self) -> str:
        """获取插件名称"""
        return self.adaptee.get_name()
    
    def get_description(self) -> str:
        """获取插件描述"""
        return self.adaptee.get_description()
    
    def execute_query(self, params=None):
        """执行查询"""
        return self.adaptee.execute_query(params)
    
    def get_required_params(self):
        """获取必需参数列表"""
        return self.adaptee.get_required_params()
```

### 6.2 迁移步骤

1. **第一阶段**：实现新的插件接口和管理器
2. **第二阶段**：为现有插件创建适配器
3. **第三阶段**：逐步替换适配器为原生实现
4. **第四阶段**：移除旧的插件加载机制

## 7. 实施计划

### 7.1 第一阶段（1-2周）

1. 设计并实现统一插件接口
2. 实现插件管理器和加载器
3. 更新配置管理器以支持插件配置
4. 创建现有插件的适配器

### 7.2 第二阶段（2-3周）

1. 逐步替换系统中直接使用插件的代码
2. 更新插件注册和加载机制
3. 实现插件生命周期管理

### 7.3 第三阶段（1周）

1. 测试所有插件功能
2. 优化性能
3. 编写文档和使用示例

## 8. 测试方案

1. **单元测试**：为每个插件接口和管理器编写单元测试
2. **集成测试**：测试插件加载、注册、执行等完整流程
3. **兼容性测试**：确保现有插件通过适配器正常工作
4. **性能测试**：评估插件系统对整体性能的影响

## 9. 风险与缓解措施

### 9.1 风险

1. **兼容性问题**：现有插件可能无法正常工作
2. **性能下降**：新的抽象层可能影响性能
3. **配置复杂性**：新的配置方式可能增加复杂性

### 9.2 缓解措施

1. **渐进式迁移**：通过适配器保证向后兼容
2. **性能监控**：在关键路径添加性能监控
3. **文档完善**：提供详细的迁移指南和使用文档