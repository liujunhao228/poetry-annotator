# Poetry Annotator

LLM 诗词情感标注工具

## 项目结构

- `src/`: 源代码目录
- `projects/`: 项目配置和数据目录（每个子目录代表一个独立项目）
- `scripts/`: 脚本目录
- `poetry-annotator-data-visualizer/`: 数据可视化工具 (可选)
- `poetry-label-editor/`: 标签编辑器 (可选)

## 功能特性

- **多项目支持**：支持管理多个独立的标注项目，每个项目拥有独立的配置、数据和处理逻辑
- **多模型支持**：支持多种大语言模型以及多种 API 格式
- **情感分类体系**：采用 17 大类、200+ 细项的中国古典诗词情感分类体系
- **多种运行模式**：提供命令行、图形界面和数据可视化三种交互方式
- **并发处理**：支持多线程并发请求，提高处理效率
- **容错机制**：具备重试、熔断等容错机制，保证任务稳定性
- **灵活配置**：支持多模型配置、数据库配置、日志配置等
- **数据可视化**：集成 Streamlit 数据可视化界面，便于分析标注结果
- **辅助工具**：提供任务分发、随机抽样、日志恢复等实用工具，以及对应的 GUI 界面

## 安装与配置

### 环境要求

- Python 3.8+
- pip 包管理工具

### 安装步骤

1. 克隆项目代码：
   ```bash
   git clone https://github.com/liujunhao228/poetry-annotator.git
   cd poetry-annotator
   ```

2. 创建虚拟环境（更推荐 `conda`）：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

### 创建和配置项目

#### 简化配置结构（推荐）

项目采用简化的两层配置结构：
- **全局配置**：`config/config.ini` - 仅指定激活项目
- **项目配置**：`projects/<项目名>/config.ini` - 包含项目所有配置

**快速开始：**

1. 在 `projects` 目录下创建一个新的项目文件夹，例如 `my_project`：
   ```bash
   mkdir projects/my_project
   ```

2. 复制项目专属的 src 目录（包含数据处理逻辑）：
   ```bash
   xcopy /E /I projects/default_project\src projects\my_project\src
   ```

3. 复制配置文件模板：
   ```bash
   copy projects/default_project\config.ini projects\my_project\config.ini
   ```

4. 创建项目类型文件（指定项目使用的标注器类型）：
   ```bash
   echo social_analysis > projects/my_project/project_type.txt
   ```

5. 在项目目录下创建必要的子目录：
   ```bash
   mkdir projects\my_project\data\source_json
   mkdir projects\my_project\data\output
   mkdir projects\my_project\logs
   ```

6. （可选）激活项目：编辑 `config/config.ini`，设置：
   ```ini
   [Project]
   active_project_config = projects/my_project/config.ini
   ```

#### 项目配置文件详解

`config.ini` 包含以下主要配置节：

**[LLM] - 大语言模型通用配置**
```ini
[LLM]
max_workers = 1              # 最大工作线程数
max_model_pipelines = 1      # 最大模型管道数
max_retries = 1              # 最大重试次数
retry_delay = 1              # 重试延迟（秒）
```

**[Logging] - 日志配置**
```ini
[Logging]
console_log_level = INFO     # 控制台日志级别
file_log_level = DEBUG       # 文件日志级别
enable_console_log = true    # 是否启用控制台日志
enable_file_log = true       # 是否启用文件日志
log_file = logs/poetry_annotator.log
max_file_size = 10           # 日志文件最大大小（MB）
backup_count = 99            # 日志文件备份数量
```

**[Database] - 数据库配置**
```ini
[Database]
db_path = poetry.db          # 数据库文件路径（相对于项目目录）
```

**[Data] - 数据路径配置**
```ini
[Data]
source_dir = data/source_json  # 源数据目录
output_dir = data/output       # 输出数据目录
```

**[Model.别名] - 模型配置**

支持配置多个模型，每个模型使用 `[Model.别名]` 格式：

```ini
[Model.DeepSeek-R1]
provider = siliconflow                           # 服务提供商
model_name = deepseek-ai/DeepSeek-R1-0528-Qwen3-8B  # 模型名称
api_key = YOUR_API_KEY                           # API 密钥
base_url = https://api.siliconflow.cn/v1/chat/completions
temperature = 1.0                                # 温度参数
max_tokens = 800                                 # 最大生成 token 数
timeout = 300                                    # 请求超时时间（秒）
```

支持的 `provider` 类型：
- `siliconflow` - 硅基流动
- `gemini` - Google Gemini
- 其他 OpenAI 兼容 API 的服务商

#### 项目目录结构

```
projects/my_project/
├── config.ini              # 项目配置文件
├── project_type.txt        # 项目类型（如 social_analysis）
├── poetry.db               # SQLite 数据库
├── data/
│   ├── source_json/        # 源数据（JSON 格式）
│   ├── output/             # 标注输出结果
│   ├── categories.xml      # 情感分类体系定义
│   └── prompt_template.txt # 提示词模板
├── logs/                   # 日志文件目录
└── src/                    # 项目专属的处理逻辑（可选）
```

#### 迁移旧版配置

如果你使用的是旧版三文件配置结构（`config.ini` + `project_config.ini`），可以运行迁移工具：

```bash
# 迁移单个项目
python scripts/migrate_config.py --project my_project

# 迁移所有项目
python scripts/migrate_config.py

# 干运行模式（仅查看变化，不修改文件）
python scripts/migrate_config.py --dry-run
```

迁移工具会：
- 合并 `config.ini` 和 `project_config.ini` 到单一的 `config.ini`
- 备份旧配置文件（添加 `.backup` 后缀）
- 更新全局配置中的激活项目设置

## 使用方法

### 命令行模式（CLI）

在使用任何命令时，都需要指定 `--project` 参数来指明操作的目标项目。

```bash
# 查看帮助信息
python main.py --help

# 启动命令行模式（默认）
python main.py --project my_project

# 初始化项目环境（例如，从 JSON 文件加载数据到数据库）
python main.py --project my_project setup --init-db

# 启动标注任务
python main.py --project my_project annotate --model gpt-4o

# 查看标注进度
python main.py --project my_project status

# 导出标注结果
python main.py --project my_project export --format jsonl
```

### 图形界面模式（GUI）

图形界面模式也已更新以支持项目管理。

```bash
# 启动图形界面
python main.py --mode gui
```

GUI 中需要在启动时或设置中指定项目名称。

### 数据可视化模式

数据可视化模式同样支持项目隔离。

```bash
# 启动数据可视化界面
python main.py --mode visualizer
```

可视化界面将根据项目配置加载相应的数据。

## 情感分类体系

本项目采用细致的情感分类体系，包含以下 17 个一级类别：

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

每个一级类别下包含若干二级类别，总计 200 多个具体的情感分类标签。

## 项目模块

### 核心功能模块

- **src/** - 核心源代码，包含标注逻辑、数据管理等
- **projects/** - 项目配置和数据（每个子目录为一个独立项目）
- **scripts/** - 辅助脚本，如任务分发、随机抽样等

### 可视化模块

- **poetry-annotator-data-visualizer/** - 基于 Streamlit 的数据可视化应用

### 辅助工具脚本

在 scripts 目录下提供了多种实用工具（推荐通过 GUI 模式使用）：

- `distribute_tasks.py` - 任务分发工具
- `random_sample.py` - 随机抽样工具
- `recover_from_log_v6.py` - 日志恢复工具
- `find_duplicate_poems.py` - 查找重复诗词工具
- `proofread_annotations.py` - 标注校对工具
- `migrate_config.py` - 配置迁移工具（将旧版配置迁移到简化结构）

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 许可证

[MIT]

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至项目维护者
