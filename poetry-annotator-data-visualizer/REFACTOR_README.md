# 诗词与标注数据可视化分析平台 (重构版)

## 项目简介

诗词与标注数据可视化分析平台是一个专门用于分析和可视化古典诗词（如唐诗、宋词）及其 AI 标注结果的工具。

**本次重构重点：**
- ✅ 分层架构：UI 层 / 服务层 / 核心层 分离
- ✅ 统一缓存：L1 内存 + L2 磁盘两级缓存
- ✅ 可测试性：核心逻辑可独立于 Streamlit 测试
- ✅ 配置外置：YAML 配置文件管理
- ✅ 组件化：可复用的 UI 组件

## 快速开始

### 安装依赖

```bash
pip install streamlit plotly pandas mlxtend pyyaml
```

### 启动应用

```bash
streamlit run main.py
```

### 运行测试

```bash
python -m pytest tests/
# 或
python -m unittest discover tests/
```

## 新架构说明

### 目录结构

```
poetry-annotator-data-visualizer/
├── config/                     # 配置文件目录
│   ├── default.yaml           # 默认配置
│   └── local.yaml             # 本地覆盖配置（可选）
├── src/                       # 重构后的源代码
│   ├── __init__.py
│   ├── core/                  # 核心业务层（无 Streamlit 依赖）
│   │   ├── __init__.py
│   │   ├── db_manager.py      # 数据库操作
│   │   ├── data_processor.py  # 数据处理
│   │   └── cache.py           # 统一缓存管理器
│   ├── services/              # 服务层（封装业务逻辑）
│   │   ├── __init__.py
│   │   ├── model_service.py   # 模型服务
│   │   ├── poem_service.py    # 诗词服务
│   │   └── emotion_service.py # 情感服务
│   ├── ui/                    # UI 层（仅 Streamlit 组件）
│   │   ├── __init__.py
│   │   ├── app.py             # Streamlit 应用入口
│   │   ├── components/        # 可复用 UI 组件
│   │   │   ├── charts.py      # 图表组件
│   │   │   ├── tables.py      # 表格组件
│   │   │   └── controls.py    # 控件组件
│   │   └── pages/             # 页面级组件
│   │       ├── single_analysis.py      # 单库分析页面
│   │       └── comparison_analysis.py  # 对比分析页面
│   └── config_loader.py       # 配置加载器
├── tests/                     # 单元测试
│   ├── __init__.py
│   └── test_core.py           # 核心模块测试
├── main.py                    # Streamlit 入口
└── apriori_interactive_miner.py  # CLI 工具（保持不变）
```

### 分层架构

```
┌─────────────────────────────────────┐
│           UI 层 (Streamlit)          │  ← 用户交互
│   ┌───────────┬───────────┐         │
│   │ Components│   Pages   │         │
│   └───────────┴───────────┘         │
├─────────────────────────────────────┤
│          服务层 (Services)           │  ← 业务逻辑
│   ┌───────────┬───────────┐         │
│   │   Model   │  Emotion  │         │
│   │   Poem    │           │         │
│   └───────────┴───────────┘         │
├─────────────────────────────────────┤
│          核心层 (Core)               │  ← 数据访问
│   ┌───────────┬───────────┐         │
│   │   DB      │  Cache    │         │
│   │ Processor │           │         │
│   └───────────┴───────────┘         │
└─────────────────────────────────────┘
```

## 核心模块说明

### 1. 核心层 (`src/core/`)

**DBManager** - 数据库管理器
```python
from src.core import DBManager

db_manager = DBManager("data/TangShi.db")
poems = db_manager.get_all_poems()
```

**DataProcessor** - 数据处理器
```python
from src.core import DataProcessor

processor = DataProcessor(db_manager)
performance = processor.compute_model_performance()
```

**CacheManager** - 统一缓存管理器
```python
from src.core import CacheManager

cache = CacheManager(".cache")
cache.set("key", dataframe, ttl=3600)
data = cache.get("key")
```

### 2. 服务层 (`src/services/`)

**ModelService** - 模型性能服务
```python
from src.services import ModelService

service = ModelService(db_manager, cache_manager)
performance = service.get_model_performance()
trends = service.get_annotation_trends(start_date, end_date)
```

**EmotionService** - 情感分析服务
```python
from src.services import EmotionService

service = EmotionService(db_manager, cache_manager)
distribution = service.get_emotion_distribution()
apriori_results = service.mine_apriori(
    level='poem',
    min_support=0.01,
    min_length=2
)
```

### 3. UI 组件 (`src/ui/components/`)

**图表组件**
```python
from src.ui.components import render_sunburst, render_bar_chart

render_sunburst(emotion_df, title="情感分布")
render_bar_chart(data, x='author', y='count', title="作者作品数")
```

**表格组件**
```python
from src.ui.components import render_model_performance_table, render_apriori_table

render_model_performance_table(perf_df)
render_apriori_table(apriori_df, top_n=20)
```

## 配置说明

### 默认配置 (`config/default.yaml`)

```yaml
database:
  paths:
    TangShi: "data/TangShi.db"
    SongCi: "data/SongCi.db"

cache:
  max_memory_items: 100
  cache_dir: ".cache"
  ttl_seconds:
    model_performance: 3600
    emotion_distribution: 3600
    apriori_results: 7200

ui:
  default_top_n: 20
  enable_custom_download: false
```

### 本地覆盖配置

创建 `config/local.yaml` 覆盖默认配置（此文件不被 git 跟踪）：

```yaml
cache:
  ttl_seconds:
    apriori_results: 14400  # 延长 Apriori 结果缓存时间
```

## 性能优化

### 缓存策略

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| 模型性能 | 1 小时 | 相对稳定 |
| 标注趋势 | 10 分钟 | 变化频繁 |
| 情感分布 | 1 小时 | 计算较重 |
| Apriori 结果 | 2 小时 | 计算密集 |

### 使用建议

1. **首次加载**：清除缓存后首次加载会较慢，属于正常现象
2. **Apriori 挖掘**：建议先使用较高支持度阈值，再逐步降低
3. **大数据集**：启用"限制最大事务数"选项控制计算规模

## 测试

### 运行单元测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试类
python -m pytest tests/test_core.py::TestCacheManager -v

# 使用 unittest
python -m unittest discover tests/
```

### 测试覆盖率

```bash
pytest --cov=src tests/
```

## 迁移指南

### 从旧版本迁移

旧代码仍然保留在 `data_visualizer/` 目录，新功能请使用新的 `src/` 模块。

**旧代码：**
```python
from data_visualizer.db_manager import DBManager
from data_visualizer.data_processor import DataProcessor
```

**新代码：**
```python
from src.core import DBManager, DataProcessor
```

### 兼容性

- 旧版 `data_visualizer/` 模块保持不变，确保向后兼容
- 新版 `src/` 模块使用相同的数据库结构
- 配置文件格式保持兼容

## 开发指南

### 添加新的可视化图表

1. 在服务层添加数据获取方法
2. 在 `src/ui/components/charts.py` 添加渲染组件
3. 在页面组件中调用

### 扩展分析功能

1. 在 `src/services/` 创建新的服务类
2. 在 `src/ui/pages/` 创建对应的页面组件
3. 在 `src/ui/app.py` 中注册

## 常见问题

### 1. 启动时提示模块导入错误

确保已安装依赖：
```bash
pip install pyyaml
```

### 2. 缓存文件位置

缓存文件存储在 `.cache/` 目录下，可安全删除。

### 3. 测试失败

确保测试数据库文件有写入权限。

## 许可证

本项目仅供学术研究使用。
