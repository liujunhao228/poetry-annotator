# 程序配置体系说明

## 概述

本项目采用分层配置管理体系，将配置分为全局配置和项目配置两个层级，以实现灵活的配置管理和多项目支持。

## 配置层级结构

### 1. 全局配置 (Global Configuration)

全局配置存储在 `config/global/config.ini` 文件中，包含系统级别的通用配置，适用于所有项目。

**主要配置项包括：**
- **LLM 配置**：并发控制、重试策略、熔断器设置等
- **数据库配置**：定义可用的数据库配置模板
- **数据路径配置**：定义可用的数据路径模板
- **情感分类体系配置**：分类体系的源文件和缓存文件路径
- **提示词配置**：默认提示词模板路径
- **日志配置**：日志级别、文件路径、轮转设置等
- **可视化配置**：数据可视化相关设置
- **模型配置**：定义多个模型的具体配置（API密钥、参数等）

### 2. 项目配置 (Project Configuration)

项目配置存储在 `config/projects/{project_name}/project.ini` 文件中，用于覆盖或指定特定项目使用的配置。

每个项目都有自己的配置目录，包含项目特定的设置：
- **数据库配置**：指定项目使用的具体数据库路径或配置名称
- **数据路径配置**：指定项目使用的具体数据路径或配置名称
- **提示词配置**：指定项目使用的具体提示词模板路径或配置名称
- **模型配置**：指定项目启用的模型列表
- **校验规则配置**：指定项目使用的校验规则集
- **预处理规则配置**：指定项目使用的预处理规则集
- **清洗规则配置**：指定项目使用的清洗规则集

### 3. 系统配置 (System Configuration)

系统配置存储在 `config/system/active_project.json` 文件中，用于管理当前激活的项目配置和所有可用的项目列表。

### 4. 规则配置 (Rules Configuration)

规则配置存储在 `config/rules/` 目录下，包含校验、预处理和清洗规则：
- **校验规则**：`config/rules/validation/`
- **预处理规则**：`config/rules/preprocessing/`
- **清洗规则**：`config/rules/cleaning/`

## 配置优先级

配置生效遵循以下优先级（从高到低）：
1. 项目配置中直接指定的路径/参数
2. 项目配置中指定的配置名称对应的全局配置
3. 全局配置中的默认值

## 配置目录结构

```
config/
├── metadata/
│   └── config_metadata.json          # 配置元数据文件
├── system/
│   ├── active_project.json           # 激活的项目配置
│   └── system_settings.json          # 系统级设置
├── global/
│   └── config.ini                    # 全局配置文件
├── projects/
│   ├── tangshi/
│   │   ├── project.ini               # 唐诗项目配置
│   │   ├── validation_rules.yaml     # 项目校验规则
│   │   ├── preprocessing_rules.yaml  # 项目预处理规则
│   │   └── cleaning_rules.yaml       # 项目清洗规则
│   ├── songci/
│   │   ├── project.ini               # 宋词项目配置
│   │   ├── validation_rules.yaml     # 项目校验规则
│   │   ├── preprocessing_rules.yaml  # 项目预处理规则
│   │   └── cleaning_rules.yaml       # 项目清洗规则
│   └── default/
│       └── project.ini               # 默认项目配置
├── rules/
│   ├── validation/
│   │   └── global_rules.yaml         # 全局校验规则
│   ├── preprocessing/
│   │   └── global_rules.yaml         # 全局预处理规则
│   └── cleaning/
│       └── global_rules.yaml         # 全局清洗规则
└── templates/
    └── prompt/                       # 提示词模板目录
```

## 配置文件详解

### config/global/config.ini (全局配置)

```ini
[LLM]
# 并发与容错控制
max_workers = 1
max_model_pipelines = 1
max_retries = 3
retry_delay = 5
breaker_fail_max = 3
breaker_reset_timeout = 60
save_full_response = true

[Database]
# 多数据库配置（按数据集分离）
db_paths = TangShi=data/TangShi.db,SongCi=data/SongCi.db
# 分离数据库配置（按数据类型分离）
separate_db_paths = raw_data=data/{main_db_name}/raw_data.db,annotation=data/{main_db_name}/annotation.db,emotion=data/{main_db_name}/emotion.db

[Data]
source_dir = data/source_json
output_dir = data/output

[Categories]
md_path = config/label/中国古典诗词主题分类体系.md
xml_path = config/label/emotion_categories.xml

[Prompt]
template_path = config/prompt/prompt_template.txt
system_prompt_instruction_template = config/prompt/system_prompt_instruction.txt
system_prompt_example_template = config/prompt/system_prompt_example.txt
user_prompt_template = config/prompt/user_prompt_template.txt

[Logging]
console_log_level = INFO
file_log_level = DEBUG
enable_file_log = True
log_file = 
enable_console_log = True
max_file_size = 100
backup_count = 9999
quiet_third_party = True

[Visualizer]
enable_custom_download = false

# 模型配置示例
[Model.qwen-max]
provider = dashscope
model_name = qwen-max
api_key = YOUR_API_KEY
base_url = https://dashscope.aliyuncs.com/compatible-mode/v1
# ... 其他模型参数
```

### config/projects/{project_name}/project.ini (项目配置)

```ini
[Database]
# 指定要使用的数据库配置名称（来自全局配置中定义的名称）
config_name = TangShi
# 或者直接指定数据库路径 (可选，优先级高于config_name)
# db_paths = TangShi=data/TangShi.db,SongCi=data/SongCi.db

[Data]
# 指定要使用的数据路径配置名称（来自全局配置中定义的名称）
config_name = default
# 或者直接指定数据路径 (可选，优先级高于config_name)
# source_dir = data/source_json
# output_dir = data/output

[Prompt]
# 指定要使用的提示词配置名称（来自全局配置中定义的名称）
config_name = default
# 或者直接指定提示词模板路径 (可选，优先级高于config_name)
# template_path = config/prompt_template.txt
# system_prompt_instruction_template = config/system_prompt_instruction.txt
# system_prompt_example_template = config/system_prompt_example.txt
# user_prompt_template = config/user_prompt_template.txt

[Model]
# 指定要使用的模型配置名称列表（来自全局配置中定义的Model.<name>节）
model_names = qwen-max,gemini-2.5-flash

[Validation]
# 指定要使用的校验规则集名称
ruleset_name = default_emotion_annotation

[Preprocessing]
# 指定要使用的预处理规则集名称
ruleset_name = social_emotion

[Cleaning]
# 指定要使用的清洗规则集名称
ruleset_name = default
```

### config/system/active_project.json (活动项目配置)

```json
{
  "active_project": "tangshi/project.ini",
  "available_projects": [
    "default/project.ini",
    "tangshi/project.ini",
    "songci/project.ini"
  ]
}
```

## 使用方式

1. **默认使用**：程序默认加载全局配置和活动项目配置（`config/system/active_project.json`中指定的项目配置）

2. **指定项目配置**：在命令行中使用 `--project <project_config_file>` 参数指定特定的项目配置文件

3. **配置管理**：通过 `ConfigManager` 类和 `ProjectConfigManager` 类进行配置的加载、修改和保存

这种配置体系设计使得系统既具备全局统一的默认配置，又能为不同项目提供灵活的定制能力，同时保持配置管理的清晰和可维护性。