# LLM诗词情感标注工具 (Poetry Annotator)

基于大语言模型的中国古典诗词情感分类标注工具。该工具旨在利用LLM对海量诗词文本进行自动化情感分类标注，支持多种模型提供商和丰富的自定义配置。

## 功能特性

- **多模型支持**：支持多种大语言模型，包括Gemini、Qwen、DeepSeek等
- **情感分类体系**：采用17大类、200+细项的中国古典诗词情感分类体系
- **多种运行模式**：提供命令行、图形界面和数据可视化三种交互方式
- **并发处理**：支持多线程并发请求，提高处理效率
- **容错机制**：具备重试、熔断等容错机制，保证任务稳定性
- **灵活配置**：支持多模型配置、数据库配置、日志配置等
- **数据可视化**：集成Streamlit数据可视化界面，便于分析标注结果
- **辅助工具**：提供任务分发、随机抽样、日志恢复等实用工具

## 目录结构

```
poetry-annotator/
├── config/                 # 配置文件目录
├── data/                   # 数据目录
├── docs/                   # 文档目录
├── ids/                    # 诗词ID文件目录
├── logs/                   # 日志目录
├── poetry-annotator-data-visualizer/  # 数据可视化模块
├── poetry-label-editor/    # 标注编辑器模块
├── scripts/                # 脚本目录
├── src/                    # 核心源代码目录
├── main.py                 # 程序入口
├── README.md               # 说明文档
└── requirements.txt        # 依赖包列表
```

## 安装与配置

### 环境要求

- Python 3.8+
- pip包管理工具

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置文件设置

1. 复制配置模板：
   ```bash
   cp config/config.ini.template config/config.ini
   ```

2. 编辑 `config/config.ini` 文件，根据需要修改以下配置：
   - LLM模型配置（API密钥、模型名称等）
   - 数据库路径
   - 日志设置
   - 情感分类体系文件路径

## 使用方法

### 命令行模式

```bash
# 查看帮助信息
python main.py --help

# 启动命令行模式（默认）
python main.py

# 指定运行模式
python main.py --mode cli
```

### 图形界面模式

```bash
# 启动图形界面
python main.py --mode gui
```

图形界面提供以下功能：
- 任务分发管理
- 随机抽样工具
- 日志恢复功能

### 数据可视化模式

```bash
# 启动数据可视化界面
python main.py --mode visualizer
```

## 情感分类体系

本项目采用细致的情感分类体系，包含以下17个一级类别：

1. 自然山水 (NatureLandscape)
2. 宴饮节庆 (BanquetFestival)
3. 童真成长 (ChildhoodGrowth)
4. 功名仕途 (CareerAmbition)
5. 家国天下 (NationWorld)
6. 羁旅漂泊 (TravelingWander)
7. 贫病疾苦 (PovertyIllness)
8. 离情别绪 (PartingEmotion)
9. 闲适隐逸 (LeisureReclusion)
10. 时空哲思 (TimeSpacePhilosophy)
11. 孤寂迷惘 (LonelinessConfusion)
12. 壮志豪情 (AmbitionHeroism)
13. 两性情思 (RomanticLove)
14. 礼教反思 (RitualCriticism)
15. 宗教艺术 (ReligionArt)
16. 生死永恒 (LifeDeathEternity)
17. 日常体悟 (DailyInsights)

每个一级类别下包含若干二级类别，总计200多个具体的情感分类标签。

## 配置说明

### 模型配置示例

支持多种模型提供商的配置：

```ini
[Model.gemini-1.5-pro]
provider = gemini
model_name = models/gemini-1.5-pro-latest
api_key = your_gemini_api_key_here

[Model.qwen-long]
provider = siliconflow
model_name = Qwen/Qwen2-7B-Instruct
api_key = your_siliconflow_api_key_here
base_url = https://api.siliconflow.cn/v1/chat/completions
```

### 数据库配置

支持单数据库和多数据库模式：

```ini
# 单数据库模式
db_path = data/poetry.db

# 多数据库模式
db_paths = TangShi=data/TangShi.db,SongCi=data/SongCi.db
```

## 项目模块

### 核心功能模块

- **src/** - 核心源代码，包含标注逻辑、数据管理等
- **scripts/** - 辅助脚本，如任务分发、随机抽样等
- **config/** - 配置文件和情感分类体系定义

### 可视化模块

- **poetry-annotator-data-visualizer/** - 基于Streamlit的数据可视化应用

### 辅助工具脚本

在scripts目录下提供了多种实用工具：

- `distribute_tasks.py` - 任务分发工具
- `random_sample.py` - 随机抽样工具
- `recover_from_log_v6.py` - 日志恢复工具
- `find_duplicate_poems.py` - 查找重复诗词工具
- `proofread_annotations.py` - 标注校对工具

## 贡献指南

欢迎提交Issue和Pull Request来改进本项目。

## 许可证

[待添加具体许可证信息]

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至项目维护者