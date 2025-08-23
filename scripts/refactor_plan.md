# 重构 scripts/ 目录以彻底拥抱分离数据库

## 目标

修改 scripts/ 目录下的所有脚本，使其能够正确识别并使用项目级和全局级配置定义的分离数据库，而不是直接连接单一的主数据库。

## 核心变更点

1.  所有脚本将通过 `src.data.manager.DataManager` (或新的 `get_data_manager`) 来访问数据，而不是直接连接数据库。
2.  利用 `DataManager` 内部已经实现的分离数据库逻辑 (通过 `SeparateDatabaseManager`) 来访问原始数据、标注数据和情感数据。
3.  修改脚本中的数据库操作逻辑，确保它们通过 `DataManager` 提供的接口访问正确的数据库。
4.  为需要访问特定数据库（如原始数据、标注数据）的脚本，提供 `db_name` 参数或配置选项。

## 具体实施计划

### 1. 依赖项注入与配置获取

*   所有脚本将使用 `src.config.config_manager.config_manager` 来获取当前激活项目的配置。
*   通过 `src.data.manager.get_data_manager(db_name)` 获取对应数据库的数据管理器实例。
*   清理脚本中直接使用 `sqlite3.connect` 或自定义数据库连接逻辑的代码。

### 2. 脚本分类与修改策略

#### A. 统计与报告类 (`annotation_statistics.py`, `data_cleaning.py`, `poem_classification.py`)

*   **功能:** 主要读取数据进行分析。
*   **修改点:**
    *   使用 `get_data_manager(db_name)` 获取数据管理器。
    *   调用 `data_manager.get_statistics()` 或 `data_manager.get_annotation_statistics()` 等方法获取数据。
    *   对于 `data_cleaning.py` 和 `poem_classification.py`，需要更新其内部的数据库查询逻辑，通过 `data_manager.db_adapter` (原始数据) 或 `data_manager.annotation_db` (标注数据) 执行。

#### B. 任务分发与执行类 (`distribute_tasks.py`)

*   **功能:** 负责启动标注任务。
*   **修改点:**
    *   确保 `Annotator` 类及其依赖的 `DataManager` 能够正确识别和使用分离数据库。
    *   脚本入口部分获取数据库路径的逻辑需要更新，以支持项目级配置和多数据库。

#### C. 数据导出类 (`export_poem_annotations.py`, `simple_api_example.py`, `simple_data_api.py`)

*   **功能:** 需要导出标注数据。
*   **修改点:**
    *   使用 `get_data_manager(db_name)` 获取数据管理器。
    *   调用 `data_manager.export_results()` 或直接通过 `data_manager.annotation_db` 查询标注数据。
    *   确保 `AnnotationDataExporter` 类（在 `src.annotation_data_exporter` 中）也已更新以使用分离数据库。

#### D. 数据查找与校对类 (`find_duplicate_poems.py`, `proofread_annotations.py`)

*   **功能:** 需要查找或校对原始诗词数据。
*   **修改点:**
    *   使用 `get_data_manager(db_name)` 获取数据管理器。
    *   通过 `data_manager.db_adapter` (原始数据数据库) 执行查询。
    *   更新 `proofread_annotations.py` 中调用的 `dm.get_completed_poem_ids` 方法，确保其通过 `data_manager.annotation_db` 查询标注状态。

#### E. 数据处理类 (`random_sample.py`)

*   **功能:** 用于随机抽样诗词。
*   **修改点:**
    *   使用 `get_data_manager(db_name)` 获取数据管理器。
    *   通过 `data_manager.db_adapter` (原始数据数据库) 执行查询。

#### F. 数据恢复类 (`recover_from_log_v6.py`, `recover_from_log_v7.py`)

*   **功能:** 需要恢复数据到标注数据库。
*   **修改点:**
    *   使用 `get_data_manager(db_name)` 获取数据管理器。
    *   调用 `data_manager.save_annotation()` 方法保存数据，确保其通过 `data_manager.annotation_db` 写入标注数据。

#### G. 配置与API封装类 (`simple_config_api.py`, `simple_data_api.py`)

*   **功能:** 为其他脚本提供简单的API。
*   **修改点:**
    *   确保 `simple_data_api.py` 中的所有方法都通过 `get_data_manager(db_name)` 获取数据管理器，并正确传递 `db_name` 参数。
    *   `simple_config_api.py` 主要与配置相关，可能只需确保其能正确获取项目级配置。

### 3. 参数化支持

*   为需要指定数据库的脚本添加 `--db-name` 命令行参数，允许用户指定要操作的数据库 (例如 `TangShi`, `SongCi`)。
*   修改脚本入口逻辑，根据 `--db-name` 参数或默认值 (`default`) 调用 `get_data_manager`。

### 4. 兼容性与测试

*   确保修改后的脚本在单数据库和多数据库配置下都能正常工作。
*   编写或更新单元测试，验证脚本在分离数据库环境下的正确性。