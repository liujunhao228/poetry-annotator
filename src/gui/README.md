# GUI 模块重构说明

## 概述

GUI 模块已从单个 884 行的 `scripts/gui_launcher.py` 文件重构为模块化、可扩展的包结构，采用分层架构和现代设计模式。

## 目录结构

```
src/gui/
├── __init__.py              # 包导出
├── __main__.py              # 支持 python -m src.gui 运行
├── app.py                   # 应用入口
├── main_window.py           # 主窗口类
├── di.py                    # 依赖注入容器
├── components/              # 可复用 UI 组件
│   ├── __init__.py
│   ├── database_selector.py # 数据库选择器
│   ├── model_selector.py    # 模型选择器
│   ├── log_panel.py         # 日志输出面板
│   ├── config_mixin.py      # 配置加载/保存混入类
│   ├── poetry_table.py      # 诗词表格
│   ├── annotation_editor.py # 标注编辑器
│   └── search_filter_bar.py # 搜索过滤栏
├── tabs/                    # 功能选项卡
│   ├── __init__.py
│   ├── base_tab.py          # 选项卡基类
│   ├── distribution_tab.py  # 任务分发
│   ├── sampling_tab.py      # 随机抽样
│   ├── recovery_tab.py      # 日志恢复
│   └── annotation_browser_tab.py  # 标注浏览
├── services/                # 服务层
│   ├── __init__.py
│   ├── task_executor.py     # 任务执行服务
│   ├── config_service.py    # 配置服务
│   └── log_service.py       # 全局日志服务
└── models/                  # 数据模型
    ├── __init__.py
    ├── config.py            # 配置数据类
    ├── config_manager.py    # 统一配置管理器
    └── state.py             # 响应式状态管理
```

## 启动方式

### 方式 1：从 Python 代码启动
```python
from src.gui import run_gui
run_gui()
```

### 方式 2：命令行模块运行
```bash
python -m src.gui
```

## 核心改进

### 1. 统一配置管理

**重构前**: 每个 Tab 独立管理配置文件
- `config/gui_distribution.json`
- `config/gui_sampling.json`
- `config/gui_recovery.json`

**重构后**: 单一配置文件 `config/gui_config.json`

```python
from src.gui.models import UnifiedConfigManager

# 创建配置管理器
config_manager = UnifiedConfigManager(Path('config/gui_config.json'))

# 访问各模块配置
dist_config = config_manager.distribution
sampling_config = config_manager.sampling

# 保存所有配置
config_manager.save()
```

### 2. 依赖注入容器

轻量级 DI 容器，管理服务生命周期：

```python
from src.gui.di import Container, build_gui_container

# 构建标准容器
container = build_gui_container(project, config_service)

# 获取服务
config_service = container.get(ConfigService)
log_service = container.get(LogService)
config_manager = container.get(UnifiedConfigManager)
```

### 3. 全局日志服务

集中管理应用日志，支持多订阅者：

```python
from src.gui.services import LogService

# 获取全局日志服务
log_service = LogService()

# 订阅日志
log_service.subscribe(lambda msg: print(msg))

# 写入日志
log_service.info("任务开始")
log_service.error("发生错误")
```

### 4. 响应式状态管理

观察者模式实现状态变化自动通知：

```python
from src.gui.models import StateManager, DistributionTabState

# 获取状态管理器
state_manager = StateManager()

# 获取特定状态
dist_state = state_manager.get_distribution_state()

# 订阅状态变化
dist_state.subscribe(lambda: update_ui())

# 更新状态
dist_state.set_field('is_running', True)
```

### 5. 分层架构

```
┌─────────────────────────────────────┐
│         MainWindow                  │  ← 表现层
│  (组合 DI 容器 + 配置管理器 + 日志服务)  │
├─────────────────────────────────────┤
│         Tabs (UI)                   │  ← 选项卡 UI
├─────────────────────────────────────┤
│         Components                  │  ← 可复用组件
├─────────────────────────────────────┤
│         Services                    │  ← 业务服务层
│  - ConfigService                    │
│  - TaskExecutor                     │
│  - LogService                       │
├─────────────────────────────────────┤
│         Models                       │  ← 数据模型层
│  - Config (dataclass)               │
│  - State (Observable)               │
└─────────────────────────────────────┘
```

## 新增文件

| 文件 | 说明 |
|------|------|
| `di.py` | 依赖注入容器 |
| `models/config_manager.py` | 统一配置管理器 |
| `models/state.py` | 响应式状态管理 |
| `services/log_service.py` | 全局日志服务 |

## 兼容性说明

- ✅ **向后兼容**: 所有 Tab 仍支持独立的配置文件
- ✅ **配置迁移**: 旧配置文件会自动保留，新配置使用统一文件
- ✅ **API 兼容**: 现有调用代码无需修改
- ✅ **渐进式重构**: 可以逐步采用新功能

## 配置迁移指南

### 从分散配置迁移到统一配置

```python
# 旧方式（仍然支持）
from src.gui.models import DistributionConfig
config = DistributionConfig.load(Path('config/gui_distribution.json'))

# 新方式（推荐）
from src.gui.models import UnifiedConfigManager
config_manager = UnifiedConfigManager()
config = config_manager.distribution  # 直接访问
```

### 在 MainWindow 中使用 DI 容器

```python
# 新方式
from src.gui.di import build_gui_container

container = build_gui_container(project)
config_service = container.get(ConfigService)
log_service = container.get(LogService)
```

## 扩展指南

### 添加新的响应式状态

```python
from src.gui.models.state import Observable

class NewFeatureState(Observable):
    is_running: bool = False
    progress: int = 0
    setting_a: str = ""
    
    def __post_init__(self):
        super().__init__()

# 在 StateManager 中添加
class StateManager:
    def __init__(self):
        self._new_feature_state = NewFeatureState()
    
    def get_new_feature_state(self) -> NewFeatureState:
        return self._new_feature_state
```

### 添加新的服务

```python
# 1. 创建服务类
class NewService:
    def do_something(self):
        pass

# 2. 在 DI 容器中注册
container.register_singleton(NewService)

# 3. 在服务层导出
# services/__init__.py
from .new_service import NewService
__all__.append("NewService")
```

## 测试验证

### 导入测试
```bash
.venv\Scripts\python.exe -c "from src.gui import run_gui; print('OK')"
```

### 配置测试
```python
from src.gui.models import UnifiedConfigManager

config_manager = UnifiedConfigManager()
config_manager.distribution.console_log_level = "DEBUG"
config_manager.save()
```

### DI 容器测试
```python
from src.gui.di import build_gui_container

container = build_gui_container(project)
assert container.has(ConfigService)
assert container.has(LogService)
```

## 性能优化

1. **配置缓存**: 配置加载后缓存在内存中
2. **单例模式**: 服务默认使用单例模式
3. **批量保存**: 窗口关闭时一次性保存所有配置
4. **异步日志**: 日志服务支持异步队列处理

## 回滚方案

如需回滚到旧版本：

```bash
# 恢复旧文件
git checkout -- src/gui/

# 删除新文件
rm src/gui/di.py
rm src/gui/models/config_manager.py
rm src/gui/models/state.py
rm src/gui/services/log_service.py
```

## 后续优化方向

1. **异步任务执行器**: 使用 asyncio 替代 threading
2. **配置热更新**: 支持配置文件变化自动重载
3. **日志持久化**: 将日志保存到文件
4. **状态快照**: 支持状态保存和恢复
