# 项目配置管理体系

## 概述

本项目采用了重构后的配置管理体系，具有清晰的层级结构和明确的职责划分。该体系将配置分为全局配置、项目配置、规则配置和系统配置等多个层次，便于管理和维护。

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

### 全局配置 (config/global/config.ini)

全局配置文件包含适用于所有项目的通用设置：

- **LLM 配置**：并发控制、重试策略、熔断器设置等
- **数据库配置**：多数据库配置、分离数据库配置模板
- **数据路径配置**：源数据和输出数据的路径
- **情感分类体系配置**：情感分类体系的 Markdown 源文件和 XML 缓存文件路径
- **提示词配置**：全局默认的提示词模板路径
- **日志系统配置**：日志级别、文件路径、轮转设置等
- **数据可视化配置**：可视化相关设置
- **模型配置**：各个模型的具体配置，包括提供商、模型名称、API 密钥等

### 项目配置 (config/projects/)

每个项目都有自己独立的配置目录，包含项目特定的设置：

#### 项目配置文件 (project.ini)

- **数据库配置**：指定要使用的数据库配置名称或直接指定数据库路径
- **数据路径配置**：指定要使用的数据路径配置名称或直接指定路径
- **提示词配置**：指定要使用的提示词配置名称或直接指定模板路径
- **模型配置**：指定要使用的模型配置名称列表
- **校验规则配置**：指定要使用的校验规则集名称
- **预处理规则配置**：指定要使用的预处理规则集名称
- **清洗规则配置**：指定要使用的清洗规则集名称

#### 项目规则文件

- **validation_rules.yaml**：项目特定的校验规则
- **preprocessing_rules.yaml**：项目特定的预处理规则
- **cleaning_rules.yaml**：项目特定的清洗规则

### 系统配置 (config/system/)

系统级别的配置文件：

- **active_project.json**：定义当前激活的项目和所有可用的项目列表

### 规则配置 (config/rules/)

包含全局规则配置：

- **validation/global_rules.yaml**：全局校验规则
- **preprocessing/global_rules.yaml**：全局预处理规则
- **cleaning/global_rules.yaml**：全局清洗规则

### 配置元数据 (config/metadata/config_metadata.json)

定义配置文件的路径和结构，是配置管理体系的核心元数据文件。

## 配置管理器

项目使用配置管理器来加载和管理所有配置：

- **ConfigManager**：核心配置管理器，负责协调全局和项目配置的加载、管理和获取
- **ProjectConfigManager**：项目配置管理器，用于管理当前激活的项目配置文件
- **RulesLoader**：规则配置处理器，处理校验、预处理、清洗等规则文件的加载

## 配置切换

项目支持在不同配置之间切换，可以通过修改 `config/system/active_project.json` 文件或使用配置管理器的 API 来切换当前激活的项目。

## 最佳实践

1. **全局配置**：将适用于所有项目的通用设置放在全局配置中
2. **项目配置**：将项目特定的设置放在对应的项目配置目录中
3. **规则配置**：将校验、预处理和清洗规则分别放在对应的规则配置文件中
4. **配置元数据**：通过 `config_metadata.json` 文件来定义配置文件的路径和结构
5. **系统配置**：将系统级别的设置放在系统配置中

## 测试

项目包含了配置管理体系的测试脚本，可以运行以下命令来验证配置管理体系是否正常工作：

```bash
python tests/test_config_detailed.py
```