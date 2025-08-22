# 配置管理体系说明

## 目录结构

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

## 配置文件说明

### 全局配置 (config/global/config.ini)

包含所有全局设置，如LLM配置、数据库配置、数据路径配置、情感分类体系配置、提示词配置、日志系统配置、数据可视化配置和模型配置等。

### 项目配置 (config/projects/)

每个项目都有自己的配置目录，包含项目特定的设置。

#### 项目配置文件 (project.ini)

包含项目特定的数据库配置、数据路径配置、提示词配置、模型配置、校验规则配置、预处理规则配置和清洗规则配置。

### 系统配置 (config/system/)

包含系统级设置，如当前激活的项目配置。

### 规则配置 (config/rules/)

包含校验、预处理和清洗规则的配置文件。

### 配置元数据 (config/metadata/config_metadata.json)

定义配置文件的路径和结构。