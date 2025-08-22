# 配置管理体系重构计划

## 当前问题分析

1. `config_metadata.json` 和 `active_project.json` 都在 config 根目录，职责不清晰
2. 项目配置文件命名不规范，层级结构不清晰
3. 配置文件的组织方式不够直观，难以维护

## 重构目标

1. 建立清晰的配置层级结构
2. 明确各配置文件的职责
3. 提高配置管理的可维护性和可扩展性

## 新的配置结构

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

## 实施步骤

1. 创建新的目录结构
2. 迁移现有配置文件到新的结构中
3. 更新配置管理器代码以适配新的结构
4. 更新文档和注释
5. 测试重构后的配置管理体系