# Poetry Annotator

LLM诗词情感标注工具

## 项目结构

- `src/`: 源代码目录
- `projects/`: 项目配置和数据目录（每个子目录代表一个独立项目）
- `scripts/`: 脚本目录
- `poetry-annotator-data-visualizer/`: 数据可视化工具 (可选)
- `poetry-label-editor/`: 标签编辑器 (可选)

## 功能特性

- **多项目支持**：支持管理多个独立的标注项目，每个项目拥有独立的配置、数据和处理逻辑
- **多模型支持**：支持多种大语言模型以及多种API格式
- **情感分类体系**：采用17大类、200+细项的中国古典诗词情感分类体系
- **多种运行模式**：提供命令行、图形界面和数据可视化三种交互方式
- **并发处理**：支持多线程并发请求，提高处理效率
- **容错机制**：具备重试、熔断等容错机制，保证任务稳定性
- **灵活配置**：支持多模型配置、数据库配置、日志配置等
- **数据可视化**：集成Streamlit数据可视化界面，便于分析标注结果
- **辅助工具**：提供任务分发、随机抽样、日志恢复等实用工具，以及对应的GUI界面

## 安装与配置

### 环境要求

- Python 3.8+
- pip包管理工具

### 安装步骤

1. 克隆项目代码：
   ```bash
   git clone https://github.com/liujunhao228/poetry-annotator.git
   cd poetry-annotator
   ```

2. 创建虚拟环境（更推荐`conda`）：
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

1. 在 `projects` 目录下创建一个新的项目文件夹，例如 `my_project`：
   ```bash
   mkdir projects/my_project
   ```

2. 在项目文件夹内创建配置文件 `config.ini`。您可以复制 `projects/default_project/config.ini` 作为模板：
   ```bash
   cp projects/default_project/config.ini projects/my_project/config.ini
   ```

3. 编辑 `projects/my_project/config.ini` 文件，根据需要修改以下配置：
   - LLM模型配置（API密钥、模型名称等）
   - 数据库路径（相对于项目目录，如 `data/poetry.db`）
   - 数据源路径（相对于项目目录，如 `data/source_json`）
   - 日志设置
   - 情感分类体系文件路径（相对于项目目录）

4. 在项目目录下创建必要的子目录（如 `data`, `logs`）并放置相关文件（诗词数据、分类体系等）。

## 使用方法

### 命令行模式（CLI）

在使用任何命令时，都需要指定 `--project` 参数来指明操作的目标项目。

```bash
# 查看帮助信息
python main.py --help

# 启动命令行模式（默认）
python main.py --project my_project

# 初始化项目环境（例如，从JSON文件加载数据到数据库）
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

## 项目模块

### 核心功能模块

- **src/** - 核心源代码，包含标注逻辑、数据管理等
- **projects/** - 项目配置和数据（每个子目录为一个独立项目）
- **scripts/** - 辅助脚本，如任务分发、随机抽样等

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
