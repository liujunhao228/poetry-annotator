# Poetry Annotator - 基于大语言模型的中国古典诗词情感分类标注工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

Poetry Annotator 是一个基于大语言模型（LLM）的中国古典诗词情感分类标注工具，旨在通过自动化方式为唐诗、宋词等古典诗词进行情感分类标注，为文学研究、情感分析等提供高质量的数据集。

## 🌟 特性

- **多模型支持**：支持多种大语言模型（Qwen、Gemini、GPT等）进行情感标注
- **插件化架构**：采用灵活的插件系统，便于扩展和定制功能
- **情感分类体系**：基于"交际维度"理论的情感分类体系，包含关系动作、情感策略、传播场景和风险等级四个维度
- **可视化分析**：提供基于Streamlit的Web可视化界面，用于分析标注结果
- **丰富的GUI工具**：包含任务分发、随机抽样、日志恢复、标注校对等功能的图形界面
- **数据管理**：支持数据库管理和数据导出功能
- **并发处理**：支持多个模型并发执行标注任务，提高处理效率

## 📋 目录结构

```
poetry-annotator/
├── config/                 # 配置文件目录
├── data/                   # 数据目录
├── docs/                   # 文档目录
├── examples/               # 示例代码
├── logs/                   # 日志目录
├── project/                # 项目配置
│   ├── label/              # 情感分类体系
│   └── plugins/            # 插件目录
├── scripts/                # 脚本目录
├── src/                    # 源代码目录
│   ├── gui/                # 图形界面模块
│   ├── plugin_system/      # 插件系统
│   └── ...                 # 其他功能模块
├── tests/                  # 测试代码
├── poetry-annotator-data-visualizer/  # 数据可视化模块
├── main.py                 # 主入口文件
└── pyproject.toml          # 项目配置文件
```

## 🚀 快速开始

### 安装依赖

```bash
# 推荐使用uv工具进行安装
pip install uv
uv sync

# 或者使用传统的pip安装
pip install -e .
```

### 配置项目

1. 复制配置文件模板：
```bash
cp config/global/config.ini.template config/global/config.ini
```

2. 编辑 `config/global/config.ini` 文件，配置您的API密钥和模型参数

3. 项目配置文件位于 `project/project.ini`，可以根据需要进行调整

### 运行工具

#### 命令行模式

```bash
# 查看帮助信息
python main.py --help

# 初始化数据库
python main.py --mode init-db

# 或者使用专门的初始化脚本（推荐）
python scripts/init_database.py

# 清空并重新初始化数据库
python scripts/init_database.py --clear

# 列出已配置的模型
python main.py list-models

# 启动标注任务
python main.py annotate --model qwen-max --limit 100

# 查看标注进度
python main.py status

# 导出标注结果
python main.py export --format jsonl --output results.jsonl
```

#### GUI模式

```bash
# 启动功能工具集GUI
python main.py --mode gui

# 启动标注校对GUI
python main.py --mode gui-review

# 启动数据可视化界面
python main.py --mode visualizer
```

## 🧠 情感分类体系

支持根据实际所需自定义情感分类体系

## 🖥️ GUI工具

### 功能工具集GUI
包含以下功能模块：
- **任务分发**: 将诗词分配给不同模型进行标注
- **随机抽样**: 从诗词库中随机抽取样本
- **日志恢复**: 从日志文件中恢复未保存的标注数据
- **标注校对**: 对标注结果进行人工校对和修正

### 标注校对GUI
专门用于对模型标注结果进行人工校对，支持：
- 浏览诗词内容
- 查看模型标注结果
- 手动修正标注
- 批量操作

## 📊 数据可视化

数据可视化模块提供基于Streamlit的Web界面，包含：

### Web可视化界面功能
- **单库分析模式**：深入分析单个诗词数据库
  - 模型性能总览
  - 标注趋势分析
  - 诗人作品数量分布
  - 诗词长度分布
  - 情感类型分析
  - 情感共现分析

- **双库对比模式**：对比分析两个诗词数据库
  - 模型性能对比
  - 标注趋势对比
  - 情感分析对比

### 命令行挖掘工具
- 交互式Apriori算法挖掘工具
- 单库情感关联规则挖掘
- 双库情感关联规则对比挖掘

启动可视化界面：
```bash
streamlit run poetry-annotator-data-visualizer/main.py
```

## 🔧 插件系统

项目采用灵活的插件系统，支持以下插件类型：
- **查询插件**: 用于执行数据查询操作
- **预处理插件**: 用于数据预处理操作
- **Prompt构建插件**: 用于构建LLM提示词
- **标签解析插件**: 用于解析和扩展标签分类
- **数据库初始化插件**: 用于数据库初始化操作

## 📈 性能优化

1. **多级缓存**: 引入了基于磁盘的持久化缓存层，用于存储耗时计算的结果
2. **并发处理**: 支持多个模型并发执行标注任务
3. **速率控制**: 内置速率控制机制，防止API调用超限
4. **错误恢复**: 支持从日志文件中恢复未保存的标注数据

## 🛠️ 开发指南

### 环境要求
- Python 3.9 或更高版本
- 支持的操作系统：Windows、Linux、macOS

### 安装开发环境
```bash
# 克隆项目
git clone <repository-url>
cd poetry-annotator

# 安装依赖
pip install uv
uv sync

# 或者使用传统的pip安装
pip install -e .
```

### 运行测试
```bash
python -m pytest tests/
```

## 📚 文档

- [插件系统文档](docs/plugin_system.md)
- [插件系统重构计划](docs/plugin_system_refactor_plan.md)
- [插件系统重构完成说明](docs/plugin_system_refactor_complete.md)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📄 许可证

本项目采用MIT许可证，详情请见[LICENSE](LICENSE)文件。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和研究人员。