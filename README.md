# LLM诗词情感标注工具 (Poetry Annotator)

基于大语言模型的中国古典诗词情感分类标注工具。该工具旨在利用LLM对海量诗词文本进行自动化情感分类标注，支持多种模型提供商和丰富的自定义配置。

## 功能特性

- **多模型支持**：支持多种大语言模型以及多种API格式，采用适配器架构设计，易于扩展
- **情感分类体系**：采用17大类、200+细项的中国古典诗词情感分类体系
- **多种运行模式**：提供命令行、图形界面和数据可视化三种交互方式
- **并发处理**：支持多线程并发请求，提高处理效率
- **容错机制**：具备重试、熔断等容错机制，保证任务稳定性
- **灵活配置**：支持多模型配置、数据库配置、日志配置等
- **数据可视化**：集成Streamlit数据可视化界面，便于分析标注结果
- **辅助工具**：提供任务分发、随机抽样、日志恢复等实用工具，以及对应的GUI界面
- **速率控制**：支持多种速率控制算法，可灵活配置QPS/RPM、并发数等参数

## 目录结构

```
poetry-annotator/
├── config/                 # 配置文件目录
├── data/                   # 数据目录
├── docs/                   # 文档目录
├── ids/                    # 诗词ID文件目录
├── logs/                   # 日志目录
├── poetry-annotator-data-visualizer/  # 数据可视化模块
├── poetry-label-editor/    # 分类定义编辑器模块
├── scripts/                # 脚本目录
├── src/                    # 核心源代码目录
├── main.py                 # 程序入口
├── README.md               # 说明文档
├── pyproject.toml          # 项目配置和依赖管理文件
└── uv.lock                 # 依赖锁定文件
```

## 安装与配置

### 环境要求

- Python 3.9+
- 包管理工具（推荐使用 `uv` 或 `pip`）

### 安装步骤

1. 克隆项目代码：
   ```bash
   git clone https://github.com/liujunhao228/poetry-annotator.git
   cd poetry-annotator
   ```

2. 创建虚拟环境（推荐使用 `uv`）：
   ```bash
   # 使用 uv 创建虚拟环境（推荐）
   uv venv
   
   # 或使用 Python 内置 venv
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .venv\Scripts\activate     # Windows
   ```

3. 安装依赖包：
   ```bash
   # 使用 uv 安装依赖（推荐）
   uv sync
   
   # 或使用 pip 安装依赖
   pip install -e .
   ```

### 配置文件设置

1. 复制配置模板：
   ```bash
   cp config/config - 副本.ini config/config.ini
   ```

2. 编辑 `config/config.ini` 文件，根据需要修改以下配置：
   - LLM模型配置（API密钥、模型名称等）
   - 数据库路径
   - 日志设置
   - 情感分类体系文件路径

4. 配置模型提供商：
   目前支持多种模型提供商，需要在配置文件中设置相应的API密钥和模型名称：
   
   ```ini
   [Model.gemini-1.5-pro]
   provider = gemini
   model_name = models/gemini-2.5-flash
   api_key = your_gemini_api_key_here
   
   [Model.qwen-long]
   provider = siliconflow # HTTP式请求
   model_name = Qwen/Qwen3-235B-A22B-Instruct-2507
   api_key = your_api_key_here
   base_url = https://api-inference.modelscope.cn/v1/chat/completions # OpenAI 格式的 API 均可
   
   # 使用DashScope(阿里云百炼)兼容OpenAI API的模型
   [Model.qwen-plus-dashscope]
   provider = dashscope
   model_name = qwen-plus
   api_key = your_dashscope_api_key_here
   enable_search = false  # DashScope特有参数
   ```
   
### 数据库配置：
   ```ini
   # 单数据库模式
   db_path = data/poetry.db

   # 多数据库模式
   db_paths = TangShi=data/TangShi.db,SongCi=data/SongCi.db
   ```

### 速率控制配置：
   ```ini
   [Model.qwen-long]
   provider = siliconflow
   model_name = Qwen/Qwen3-235B-A22B-Instruct-2507
   api_key = your_api_key_here
   # 支持QPS或RPM速率限制（二选一）
   rate_limit_qps = 1
   # rate_limit_rpm = 60
   # 最大并发请求数
   # max_concurrent = 2
   # 突发容量
   # rate_limit_burst = 5
   # 请求间延迟（秒）
   request_delay = 1.0
   ```

### 数据库初始化

项目支持多种数据库初始化方式，可以根据需要选择：

```bash
# 方式1: 使用主程序命令初始化所有配置的数据库
python main.py --mode init-db

# 方式2: 使用专门的初始化脚本
python scripts/init_databases.py

# 方式3: 初始化单个数据库（使用旧版脚本）
python scripts/init_database.py
```

数据库初始化会根据配置文件中的`db_path`或`db_paths`设置创建相应的数据库文件，并建立必要的表结构。
对于多数据库模式，系统会为每个配置的数据库创建独立的文件，并初始化相同的表结构。

## 使用方法

### 准备数据

在开始标注之前，需要准备诗词数据（[chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)）并复制至对应目录：
例如`data\source_json\TangShi`、`data\source_json\SongCi`
之后程序会自行初始化数据库并导入数据

### 命令行模式（不推荐）

```bash
# 查看帮助信息
python main.py --help

# 启动命令行模式（默认）
python main.py

# 指定运行模式
python main.py --mode cli
```

### 图形界面模式（推荐使用）

```bash
# 启动图形界面
python main.py --mode gui
```

图形界面提供以下功能：
- 任务分发管理
- 随机抽样工具
- 日志恢复功能
- 实时监控标注进度

### 数据可视化模式

```bash
# 启动数据可视化界面
python main.py --mode visualizer
```

数据可视化界面提供以下功能：
- 标注结果统计分析
- 情感分类分布图表
- 标注质量评估
- 导出分析报告

### 速率控制监控

```bash
# 查看速率控制统计信息
python main.py rate-stats
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
您可以使用`poetry-label-editor`模块来快速编辑：
```bash
python poetry-label-editor/editor_app_refactored.py
```

## 项目模块

### 核心功能模块

- **src/** - 核心源代码，包含标注逻辑、数据管理等
- **scripts/** - 辅助脚本，如任务分发、随机抽样等
- **config/** - 配置文件和情感分类体系定义

### 可视化模块

- **poetry-annotator-data-visualizer/** - 基于Streamlit的数据可视化应用

### 辅助工具脚本

在scripts目录下提供了多种实用工具（推荐通过GUI模式使用）：

- `distribute_tasks.py` - 任务分发工具
- `random_sample.py` - 随机抽样工具
- `recover_from_log_v6.py` - 日志恢复工具
- `find_duplicate_poems.py` - 查找重复诗词工具
- `proofread_annotations.py` - 标注校对工具

## 贡献指南

欢迎提交Issue和Pull Request来改进本项目。

## 许可证

[MIT]

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至项目维护者