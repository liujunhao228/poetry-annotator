# 数据管理模块

该模块负责项目的数据存储、访问和分析功能，采用分离数据库设计，支持灵活的插件化查询架构。

## 目录结构

```
src/data/
├── adapter.py                 # 数据库适配器
├── enhanced_manager.py        # 增强型数据管理器
├── exceptions.py              # 自定义异常
├── manager.py                 # 数据管理器
├── models.py                  # 数据模型（dataclass）
├── models_sqlalchemy.py       # 数据模型（SQLAlchemy）
├── separate_databases.py       # 分离数据库管理
├── plugin_interface.py        # 插件接口定义
├── plugin_query_manager.py    # 插件化查询管理器
├── plugin_query_example.py    # 插件化查询使用示例
├── plugins/                   # 查询插件目录
│   └── custom_query_plugin.py      # 自定义查询插件示例
└── sql/                   # SQL脚本目录
    ├── schema.sql             # 数据库表结构定义
    ├── init_emotion_categories.sql  # 初始化情感分类数据
    └── queries.sql            # 常用查询语句示例
```

## 数据库设计

### 分离数据库结构

本项目采用分离数据库设计，将不同类型的数据存储在不同的数据库文件中：

1. **原始数据数据库** (`raw_data.db`)：存储诗词和作者的原始数据
2. **标注数据数据库** (`annotation.db`)：存储模型标注结果数据
3. **情感分类数据库** (`emotion.db`)：存储情感分类体系数据

这种设计有以下优势：
- 提高数据访问效率
- 便于数据维护和备份
- 支持不同数据类型的不同访问模式

### 表结构

数据库表结构定义在 `sql/schema.sql` 文件中，主要包括：

- `poems`：诗词数据表
- `authors`：作者数据表
- `annotations`：标注结果表
- `sentence_annotations`：句子标注表
- `sentence_emotion_links`：句子情感链接表
- `emotion_categories`：情感分类表

## 插件化查询架构

为了实现灵活的查询逻辑定制，我们设计了插件化查询架构。

### 核心组件

1. **QueryPlugin** (`plugin_interface.py`)：查询插件抽象基类
2. **QueryPluginManager** (`plugin_interface.py`)：查询插件管理器
3. **PluginBasedQueryManager** (`plugin_query_manager.py`)：插件化查询管理器

### 内置插件

1. **CustomQueryPlugin** (`plugins/custom_query_plugin.py`)：自定义查询示例

### 使用方法

```python
from src.data.enhanced_manager import EnhancedDataManager
from src.data.plugins.custom_query_plugin import CustomQueryPlugin

# 初始化数据管理器
data_manager = EnhancedDataManager("data/poetry.db")

# 注册自定义插件
custom_plugin = CustomQueryPlugin("data/poetry.db")
data_manager.plugin_query_manager.register_plugin(custom_plugin)

# 执行查询
df = data_manager.execute_plugin_query("emotion_distribution")
```

## SQL脚本使用

### 初始化数据库

```bash
# 初始化表结构
sqlite3 data/poetry.db < src/data/sql/schema.sql

# 初始化情感分类数据
sqlite3 data/poetry.db < src/data/sql/init_emotion_categories.sql
```

### 执行查询

```bash
# 执行查询示例
sqlite3 data/poetry.db < src/data/sql/queries.sql
```

## 扩展自定义插件

要创建自定义查询插件，需要：

1. 继承 `QueryPlugin` 抽象基类
2. 实现 `get_name`、`get_description`、`execute_query` 和 `get_required_params` 方法
3. 注册插件到 `PluginBasedQueryManager`

示例：
```python
from src.data.plugin_interface import QueryPlugin

class MyCustomPlugin(QueryPlugin):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.name = "my_custom_query"
        self.description = "我的自定义查询"
    
    def get_name(self) -> str:
        return self.name
    
    def get_description(self) -> str:
        return self.description
    
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        # 实现查询逻辑
        pass
    
    def get_required_params(self) -> List[str]:
        return []
```