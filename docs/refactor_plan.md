# Poetry Annotator 重构计划

## 1. 重构目标

根据《重构要求.md》中的指示，本次重构的目标是：
1.  **简化配置管理体系**：移除冗余的配置层级，明确项目级和全局级配置的职责划分。
2.  **构建完善的数据管理体系**：将数据相关的逻辑（结构定义、数据库管理、初始化等）集中到项目层级，提升模块化和可维护性。

## 2. 配置管理体系重构

### 2.1. 现状分析

当前配置管理体系结构复杂，包含多个层级：
- `config/global/`: 全局配置，包含模型、数据库模板、数据路径等基础设置。
- `config/system/`: 系统级配置，如 `active_project.json` 用于指定当前激活的项目。
- `config/projects/`: 项目级配置，存放各个项目的具体设置。
- `config/rules/`: 规则配置，原计划用于存放全局规则，但后续计划调整。
- `config/metadata/`: 配置元数据，定义配置文件路径。
- `config/label/`: 情感分类体系文件（未在管理体系中统一管理）。

### 2.2. 重构计划

#### 2.2.1. 简化目录结构

- **移除**：
  - `config/system/` 目录及其下的 `active_project.json` 和 `system_settings.json`。项目激活逻辑将简化，直接加载 `project` 目录下的配置。
  - `config/metadata/` 目录及其下的 `config_metadata.json`。配置路径信息将硬编码或通过更简洁的方式管理。
  - `config/rules/` 目录。全局规则集将被移除，所有规则集定义将移至项目层级。
- **保留并调整**：
  - `config/global/` 目录，但仅保留模型配置、日志配置、速率与熔断器配置等真正全局性的设置。
  - `config/projects/` 目录，作为项目配置的核心。每个项目目录下将包含该项目的所有配置，包括数据源、数据库路径、规则集等。
  - `config/label/` 目录，将其纳入配置管理体系，作为项目可引用的资源。

#### 2.2.2. 配置加载逻辑调整

- **全局配置 (`config/global/config.ini`)**：
  - 保持不变，继续提供模型、日志等基础配置。
- **项目配置**：
  - 移除对 `config/system/active_project.json` 的依赖。
  - 修改 `ConfigManager`，使其默认加载 `project/project.ini`（相对于程序根目录）作为项目配置文件。
  - 项目配置文件 (`project/project.ini`) 将包含：
    - 数据库路径 (`db_path` 或 `db_paths`)。
    - 数据源路径 (`source_dir`, `output_dir`)。
    - 项目特定的模型配置引用或覆盖。
    - 项目特定的规则集文件路径（校验、预处理、清洗）。
- **插件配置**：
  - 移除 `config/plugins.ini`。
  - 插件配置将统一由 `project/plugins.ini` 管理。

#### 2.2.3. 规则集管理

- **移除全局规则集**：
  - `config/rules/` 目录下的所有文件将被删除。
- **项目级规则集**：
  - 在 `project/` 目录下创建 `rules/` 子目录。
  - 校验、预处理、清洗规则集文件将存放于 `project/rules/` 下，例如 `project/rules/validation.yaml`, `project/rules/preprocessing.yaml`。

#### 2.2.4. 情感分类体系

- `config/label/` 目录将被保留。
- 项目配置文件 (`project/project.ini`) 中应包含指向情感分类体系文件的路径配置，以便项目可以灵活引用不同的分类体系。

### 2.3. 文件变更清单

- **新增**：
  - `project/project.ini`: 项目主配置文件。
  - `project/rules/`: 项目规则集目录。
  - `project/rules/validation.yaml`: 项目校验规则。
  - `project/rules/preprocessing.yaml`: 项目预处理规则。
  - `project/rules/cleaning.yaml`: 项目清洗规则。
- **修改**：
  - `src/config/config_manager.py`: 修改配置加载逻辑，移除对 `system` 和 `metadata` 的依赖，改为加载 `project/project.ini`。
  - `src/project_system.py`: 修改插件配置加载逻辑，移除对全局 `config/plugins.ini` 的加载，仅加载 `project/plugins.ini`。
- **删除**：
  - `config/system/`
  - `config/metadata/`
  - `config/rules/`
  - `config/plugins.ini`

## 3. 数据管理体系重构

### 3.1. 现状分析

数据管理逻辑分散在 `src/data/` 模块中，部分初始化逻辑在 `scripts/` 中。数据库配置和数据路径配置通过配置管理体系获取。

### 3.2. 重构计划

#### 3.2.1. 集中数据逻辑到项目层级

- **数据结构定义**：
  - 数据库表结构定义（如 `src/data/models.py` 中的 `Poem`, `Author`, `Annotation`）将继续保留在 `src/data/` 中，作为核心数据模型。
- **数据库管理**：
  - 数据库连接、适配器 (`src/data/adapter.py`) 和管理器 (`src/data/manager.py`) 的核心逻辑保留在 `src/data/`。
  - 但数据库的初始化逻辑（`src/data/initializer.py`）将被重构，使其更紧密地与项目配置结合。
- **数据库初始化**：
  - 将 `scripts/init_databases.py` 和 `scripts/init_database.py` 的核心逻辑迁移或重构，使其能够通过项目配置 (`project/project.ini`) 获取数据库路径和数据源路径。
  - 可能创建一个新的项目级脚本或模块（例如 `project/init.py` 或在 `src/data/` 中增强现有初始化器）来处理项目数据的初始化。
- **数据导入**：
  - 待标注数据的导入逻辑 (`DataManager.load_data_from_json`, `DataManager.load_all_json_files`, `DataManager.batch_insert_poems` 等) 将继续在 `src/data/manager.py` 中，但数据源路径将严格从 `project/project.ini` 获取。

#### 3.2.2. 明确配置依赖

- 所有与数据相关的配置（数据库路径、数据源目录）都必须在 `project/project.ini` 中明确定义。
- `src/data/manager.py` 在初始化时，将直接或通过重构后的 `ConfigManager` 读取 `project/project.ini` 来获取这些路径。

### 3.3. 文件变更清单

- **修改**：
  - `src/data/manager.py`: 确保在初始化时从 `project/project.ini` 获取 `source_dir` 和数据库路径。
  - `src/data/initializer.py`: （可选）重构或增强，使其更易于通过项目配置驱动。
  - `src/config/config_manager.py`: 确保能正确读取 `project/project.ini` 中的数据相关配置。
- **可能新增**：
  - `project/init.py`: （可选）一个项目级的初始化脚本或模块，封装数据初始化逻辑。

## 4. 实施步骤

1.  **备份**：对现有 `config/` 和 `src/data/` 目录进行备份。
2.  **配置体系重构**：
    1.  创建 `project/project.ini`，迁移必要的项目配置项。
    2.  创建 `project/rules/` 目录及示例规则文件。
    3.  修改 `src/config/config_manager.py` 和 `src/project_system.py` 的配置加载逻辑。
    4.  删除 `config/system/`, `config/metadata/`, `config/rules/`, `config/plugins.ini`。
3.  **数据体系重构**：
    1.  修改 `src/data/manager.py`，使其在初始化时从 `project/project.ini` 读取数据源和数据库路径。
    2.  （可选）创建或重构初始化逻辑，使其更易于项目驱动。
4.  **测试**：全面测试配置加载、插件加载、数据初始化和标注流程，确保重构后功能正常。
5.  **文档更新**：更新 `README.md` 和相关文档，反映新的配置和数据管理方式。

## 5. 预期收益

- **配置更清晰**：目录结构简化，配置加载逻辑更直接，易于理解和维护。
- **项目隔离性增强**：每个项目拥有独立的配置和规则集，避免全局配置污染。
- **数据管理更集中**：数据相关的逻辑和配置集中在项目层级，便于项目独立部署和管理。
- **可维护性提升**：减少了冗余代码和配置文件，降低了维护成本。