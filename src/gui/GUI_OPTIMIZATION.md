# GUI UI/UX 优化说明

## 优化概述

本次优化采用 **方案 A（轻量级优化）**，在保持 Tkinter 框架的基础上，引入 `ttkbootstrap` 库进行现代化升级。

---

## 主要改进

### 1. 主题与样式升级

**新增文件：**
- `src/gui/styles/theme.py` - 主题系统
- `src/gui/styles/__init__.py` - 样式模块入口

**颜色系统：**
```python
PRIMARY = "#0078D4"       # 微软蓝 - 主色调
SUCCESS = "#107C10"       # 成功绿
WARNING = "#FFB900"       # 警告黄
DANGER = "#D13438"        # 错误红
INFO = "#00B7C3"          # 信息蓝
```

**主题特性：**
- 使用 `ttkbootstrap` 的 "litera" 主题（清新现代风格）
- 统一字体配置（Segoe UI）
- 标准化间距和边框系统

---

### 2. 布局优化

**主窗口改进：**
- 窗口尺寸：850x700 → **1200x800**（响应式）
- 最小尺寸：1024x768（适配笔记本）
- 窗口位置持久化（保存/恢复）
- 选项卡使用 `grid` 布局，支持动态调整

**选项卡布局重构：**
```
┌─────────────────────────────────────────────┐
│  配置面板 (卡片式分组)                       │
├─────────────────────────────────────────────┤
│  控制按钮 (开始/停止 + 状态指示器)            │
├─────────────────────────────────────────────┤
│  日志面板 (带边框和工具栏)                   │
├─────────────────────────────────────────────┤
│  状态栏 (进度条 + 状态信息)                  │
└─────────────────────────────────────────────┘
```

---

### 3. 组件交互增强

#### PoetryTable（诗词表格）
- ✓ 斑马纹行背景（交替颜色）
- ✓ 悬停高亮效果
- ✓ 状态颜色编码（成功绿/失败红）
- ✓ 分页控制器样式优化
- ✓ 列宽自适应

#### SearchFilterBar（搜索栏）
- ✓ 卡片式布局
- ✓ 统一的输入框和下拉框宽度
- ✓ 搜索/重置按钮右侧对齐
- ✓ 回车键触发搜索

#### AnnotationEditorDialog（标注编辑器）
- ✓ 现代化对话框样式
- ✓ 圆角复选框（`round-toggle` 样式）
- ✓ 可滚动句子编辑区
- ✓ 快捷键支持（Ctrl+S 保存，Esc 取消）

#### LogPanel（日志面板）
- ✓ 日志级别颜色高亮（DEBUG/INFO/WARNING/ERROR）
- ✓ 工具栏（清空/导出按钮）
- ✓ 日志导出功能
- ✓ 等宽字体（Consolas）

---

### 4. 全局快捷键系统

**新增文件：**
- `src/gui/utils/shortcuts.py` - 快捷键管理器

**全局快捷键：**
| 快捷键 | 功能 |
|--------|------|
| `Ctrl+S` | 保存配置 |
| `Ctrl+R` | 刷新数据 |
| `Ctrl+F` | 打开搜索 |
| `F5` | 重新加载 |
| `Esc` | 取消/关闭对话框 |

**表格快捷键：**
| 快捷键 | 功能 |
|--------|------|
| `Enter` | 编辑选中行 |
| `Ctrl+C` | 复制 ID |
| `Delete` | 删除（提示暂不支持） |

---

### 5. 右键菜单

**表格右键菜单：**
- 复制 ID
- 编辑标注
- 查看日志
- 删除（禁用）

**日志区域右键菜单：**
- 复制选中内容
- 清空日志
- 导出日志

---

### 6. 视觉优化

**选项卡标题：**
- 📤 任务分发
- 🎲 随机抽样
- 🔄 日志恢复
- 📖 标注浏览

**状态指示器：**
- ● 就绪（绿色）
- ● 运行中（黄色脉冲）
- ● 错误（红色）

**按钮样式：**
- 开始任务：`SUCCESS` 样式（绿色）
- 停止任务：`DANGER` 样式（红色）
- 浏览/导出：`OUTLINE` 样式（轮廓）

**分组框图标：**
- 🗄️ 数据库选择
- 🤖 模型选择
- 📋 ID 来源
- ⚙️ 高级选项
- 🔍 搜索过滤
- ✏️ 情感标注编辑

---

## 技术实现

### 依赖
```toml
[dependencies]
ttkbootstrap = ">=1.10.0"
```

### 核心类继承关系
```
MainWindow → ttkbootstrap.Window
BaseTab → ttkbootstrap.Frame
DistributionTab/SamplingTab/RecoveryTab → BaseTab
AnnotationBrowserTab → ttkbootstrap.Frame
PoetryTable → ttkbootstrap.Frame
SearchFilterBar → ttkbootstrap.Frame
AnnotationEditorDialog → ttkbootstrap.Window
LogPanel → ttkbootstrap.Frame
```

### 主题应用
```python
from src.gui.styles import theme

# 在窗口初始化时应用主题
theme.apply_theme(self)
```

---

## 启动方式

```bash
# 方式 1：模块运行
uv run python -m src.gui

# 方式 2：代码调用
from src.gui import run_gui
run_gui()
```

---

## 向后兼容性

- 所有配置持久化逻辑保持不变
- 外部脚本调用接口不变
- 数据模型和服务层无变更
- 仅 UI 层和交互优化

---

## 效果对比

| 维度 | 优化前 | 优化后 |
|------|--------|--------|
| 窗口尺寸 | 850x700 | 1200x800 |
| 主题 | 默认 Tkinter | ttkbootstrap (litera) |
| 颜色系统 | 单调灰/白 | 完整调色板 |
| 字体 | 系统默认 | Segoe UI / Consolas |
| 快捷键 | 无 | 全局 + 上下文 |
| 右键菜单 | 无 | 表格/日志 |
| 状态反馈 | 文本 | 颜色 + 图标 + 进度条 |
| 表格样式 | 基础 | 斑马纹 + 悬停 + 高亮 |

---

## 后续优化建议

1. **可拖动分割面板** - 使用 `ttk.PanedWindow` 实现
2. **加载动画** - 任务执行时显示进度动画
3. **Toast 提示** - 轻量级操作反馈
4. **暗色主题** - 提供主题切换选项
5. **响应式布局** - 适配不同屏幕尺寸

---

## 文件变更清单

### 新增文件
- `src/gui/styles/theme.py`
- `src/gui/styles/__init__.py`
- `src/gui/utils/shortcuts.py`
- `src/gui/utils/__init__.py`
- `src/gui/GUI_OPTIMIZATION.md`

### 修改文件
- `pyproject.toml` - 添加 ttkbootstrap 依赖
- `src/gui/main_window.py` - 主题和响应式布局
- `src/gui/tabs/base_tab.py` - 样式和布局升级
- `src/gui/tabs/distribution_tab.py` - 卡片式布局
- `src/gui/tabs/sampling_tab.py` - 卡片式布局
- `src/gui/tabs/recovery_tab.py` - 卡片式布局
- `src/gui/tabs/annotation_browser_tab.py` - 右键菜单和快捷键
- `src/gui/components/poetry_table.py` - 样式增强
- `src/gui/components/search_filter_bar.py` - 样式增强
- `src/gui/components/annotation_editor.py` - 样式增强
- `src/gui/components/log_panel.py` - 样式增强
- `src/gui/components/database_selector.py` - 样式增强
- `src/gui/components/model_selector.py` - 样式增强

---

## 测试验证

```bash
# 模块导入测试
uv run python -c "from src.gui.main_window import MainWindow; print('OK')"

# 完整启动测试
uv run python -m src.gui
```
