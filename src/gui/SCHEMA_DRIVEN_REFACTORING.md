# GUI Schema 驱动重构完成报告

## 重构概述

本次重构将 GUI 程序从硬编码的数据结构转换为 Schema 驱动架构，使其能够完整支持项目自定义数据结构。

## 核心变更

### 1. 新增文件

#### 核心模型层
- `src/gui/models/schema_definition.py` - 项目 Schema 定义
  - `SchemaField` - 字段定义数据类
  - `ProjectSchema` - 项目 Schema 容器类

#### 组件层
- `src/gui/components/dynamic_annotation_form.py` - 动态表单组件
  - 根据 Schema 自动生成 UI 控件
  - 支持 single_select, multi_select, text, number 字段类型

### 2. 重构文件

#### 模型层
- `src/gui/models/annotation_state.py`
  - `SentenceState` - 使用 `annotations` 字典存储动态字段
  - `AnnotationState` - 添加 `schema` 属性支持

#### ViewModel 层
- `src/gui/viewmodels/annotation_editor_vm.py`
  - 移除硬编码的 `tag_categories` 参数
  - 改用 `ProjectSchema` 驱动
  - 通用字段操作方法：`set_annotation_value()`, `get_annotation_value()`

#### 组件层
- `src/gui/components/annotation_editor.py`
  - 使用 `DynamicAnnotationForm` 替代 `SentenceDetailEditor`
  - 新增 `SchemaBatchOperationBar` 支持 Schema 驱动的批量操作
  - 移除 `emotion_categories` 参数，改用 `project_schema`

- `src/gui/components/annotation/sentence_overview_table.py`
  - 支持动态列定义
  - 根据 Schema 字段自动生成表格列

#### 服务层
- `src/gui/services/config_service.py`
  - 新增 `get_project_schema()` 方法
  - 新增 `get_project_type()` 方法
  - Schema 缓存机制

#### 选项卡层
- `src/gui/tabs/annotation_browser_tab.py`
  - 传递 `project_schema` 给编辑器
  - 移除对 `LabelParser` 的直接依赖

## 架构对比

### 重构前
```
GUI 组件 → 硬编码字段 (relationship_action, emotional_strategy)
         ↓
项目 Schema (四维：RA, ES, SC, RS) → 信息丢失
```

### 重构后
```
GUI 组件 → ProjectSchema → 动态字段生成
         ↓
项目 Schema (任意维度) → 完整支持
```

## 向后兼容性

以下旧组件保留但不再被新代码使用：
- `SentenceDetailEditor` - 旧版详情编辑器
- `BatchOperationBar` - 旧版批量操作栏

这些组件仍然可以被其他代码使用，但新的 `AnnotationEditorDialog` 使用新的动态组件。

## 使用示例

### 加载项目 Schema
```python
from src.gui.models.schema_definition import ProjectSchema

schema = ProjectSchema.from_project_type("social_analysis")
print(schema.field_ids)  # ['relationship_action', 'emotional_strategy', 
                         #  'communication_scene', 'risk_level']
```

### 创建标注编辑器
```python
# 获取项目 Schema
project_schema = config_service.get_project_schema()

# 创建编辑器
editor = AnnotationEditorDialog(
    parent,
    poem_data=poem_data,
    project_schema=project_schema,
    on_save=save_callback
)
```

### ViewModel 操作
```python
vm = AnnotationEditorViewModel(project_schema=schema)
vm.load_poem_data(poem_data)

# 通用字段操作
vm.set_annotation_value("relationship_action", "RA03")
vm.set_annotation_value("communication_scene", ["SC01", "SC02"])

# 获取字段定义
field_def = vm.get_field_definition("relationship_action")
print(field_def.name_zh)  # "关系动作"
```

## 新增项目类型指南

要为项目添加新的数据结构：

1. 创建项目类型目录 `src/projects/my_project_type/`
2. 定义 Schema：
   ```python
   class MyProjectSchema(BaseAnnotationSchema):
       def _build_schema(self) -> Dict[str, Any]:
           return {
               "my_field": {
                   "id": "my_field",
                   "name_zh": "我的字段",
                   "categories": [...]
               }
           }
   ```
3. 在 `src/projects/__init__.py` 中注册
4. 在项目的 `project_type.txt` 中指定类型

GUI 将自动适配新的数据结构，无需修改任何 GUI 代码。

## 测试验证

运行测试脚本验证核心功能：
```bash
uv run python -c "
from src.gui.models.schema_definition import ProjectSchema
schema = ProjectSchema.from_project_type('social_analysis')
print(f'Schema: {schema.project_type}, 字段：{schema.field_ids}')
"
```

## 后续工作

1. **UI 测试** - 手动运行 GUI 程序验证 UI 渲染正确
2. **数据迁移** - 处理旧格式标注数据的兼容性问题
3. **文档更新** - 更新用户手册和开发者文档
4. **性能优化** - 对于大量字段的情况优化 UI 渲染

## 文件清单

### 新增文件
- `src/gui/models/schema_definition.py`
- `src/gui/components/dynamic_annotation_form.py`

### 修改文件
- `src/gui/models/annotation_state.py`
- `src/gui/models/__init__.py`
- `src/gui/viewmodels/annotation_editor_vm.py`
- `src/gui/viewmodels/__init__.py`
- `src/gui/components/annotation_editor.py`
- `src/gui/components/__init__.py`
- `src/gui/components/annotation/__init__.py`
- `src/gui/components/annotation/sentence_overview_table.py`
- `src/gui/services/config_service.py`
- `src/gui/tabs/annotation_browser_tab.py`

### 删除文件（旧版代码）
- `src/gui/components/annotation/batch_operation_bar.py`
- `src/gui/components/annotation/sentence_detail_editor.py`

---

重构完成日期：2026 年 3 月 29 日
