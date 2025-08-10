# Poetry Annotator - LLM 诗词情感标注工具

Poetry Annotator 是一个功能强大的工具，旨在利用大型语言模型（LLM）对中国古典诗词进行精细化的情感标注。它集成了高并发处理、多模型支持、强大的容错机制和友好的用户界面，为大规模诗词情感分析研究提供了坚实的基础。

![GUI界面](https://user-images.githubusercontent.com/assets/12345/some-image-url.png) 
<!-- 一张GUI界面的截图 -->

## ✨ 核心特性

- **多模型支持**:
  - 内置支持 **Gemini** 和 **SiliconFlow** (兼容OpenAI API)，可轻松扩展以支持更多LLM提供商。
  - 允许在配置文件中定义多个模型，并为每个模型设置独立的API参数、速率限制和提示词模板。

- **高性能与高并发**:
  - **异步架构**: 基于 `asyncio` 和 `httpx`，实现高效的I/O操作。
  - **并发控制**: 可配置的并发工作线程（`max_workers`）和模型管道（`max_model_pipelines`），充分利用硬件和API配额。
  - **速率限制**: 内置异步令牌桶算法（`AsyncTokenBucket`），精确控制QPS，防止超出API频率限制。

- **强大的容错与稳定性**:
  - **自动重试**: 使用 `tenacity` 实现带随机抖动的指数退避重试策略，优雅处理网络波动和临时性API错误。
  - **熔断器机制**: 集成 `pybreaker`，在服务持续失败时自动“熔断”，避免资源浪费，并在服务恢复后自动重试。
  - **健壮的响应解析**: 内置强大的 `LLMResponseParser`，能够处理不规范的LLM输出（如Markdown代码块、额外的解释文本、非标准JSON等），并对解析结果进行业务层面的有效性验证。
  - **任务断点续传**: `distribute_tasks.py` 脚本支持进度缓存，即使任务中断，也可以从上次完成的批次继续，无需从头开始。

- **灵活的任务管理**:
  - **命令行接口 (CLI)**: 提供基于 `click` 的全功能命令行工具，支持项目初始化、模型管理、启动标注、查看状态和导出结果。
  - **图形用户界面 (GUI)**: 提供基于 `Tkinter` 的`gui_launcher.py`，让不熟悉命令行的用户也能轻松配置和运行“任务分发”和“随机抽样”等复杂任务。
  - **任务分发器**: `distribute_tasks.py` 脚本能够读取ID文件列表，将其分发给一个或多个模型进行大规模并行处理。

- **高度可配置**:
  - **中心化配置**: 所有配置项（数据库、路径、日志、LLM参数等）均在 `config/config.ini` 中统一管理。
  - **可定制提示词**: 支持全局和模型特定的提示词模板，轻松为不同模型优化Prompt。
  - **分级日志系统**: 可为控制台和文件设置不同级别的日志，支持日志轮转和第三方库日志静音，便于调试和监控。

- **完善的数据流**:
  - **数据初始化**: 从指定的JSON源文件一键初始化SQLite数据库。
  - **随机抽样**: `random_sample.py` 脚本可以从数据库中随机抽取指定数量的诗词ID，用于创建测试集或分发任务。
  - **结果导出**: 轻松将标注结果导出为 `jsonl` 等格式，方便后续分析。



## 🏛️ 项目结构

```
poetry-annotator/
├── config/
│ ├── config.ini # 主配置文件 (需从模板创建)
│ ├── config.ini.template # 配置文件模板
│ ├── emotion_categories.xml # （自动生成）情感体系XML缓存
│ ├── 中国古典诗词情感分类体系.md # 情感分类体系定义文件
│ ├── system_prompt_instruction.txt # 默认系统提示-指令部分
│ ├── system_prompt_example.txt # 默认系统提示-示例部分
│ └── user_prompt_template.txt # 默认用户提示模板
├── data/
│ ├── source_json/ # 存放原始诗词JSON数据
│ │ ├── author.song.json
│ │ └── ci.song.*.json
│ ├── output/ # 存放导出的结果文件
│ └── ids/ # （示例）存放抽样的ID文件
├── logs/ # 存放日志文件
├── src/ # 项目源代码
│ ├── llm_services/ # LLM服务实现
│ │ ├── base_service.py
│ │ ├── gemini_service.py
│ │ └── siliconflow_service.py
│ ├── utils/ # 工具模块
│ │ ├── health_checker.py
│ │ └── rate_limiter.py
│ ├── annotator.py # 单模型标注器
│ ├── config_manager.py # 配置管理器
│ ├── data_manager.py # 数据管理器 (SQLite)
│ ├── label_parser.py # 情感体系解析器
│ ├── llm_factory.py # LLM服务工厂
│ ├── llm_response_parser.py # 健壮的LLM响应解析器
│ ├── logging_config.py # 日志配置模块
│ └── main.py # CLI主入口
├── .progress_cache/ # （自动生成）任务进度缓存
├── main.py # 项目主入口
├── init_database.py # 数据库初始化脚本
├── distribute_tasks.py # 高级任务分发脚本
├── random_sample.py # 随机抽样脚本
└── gui_launcher.py # 图形用户界面启动器
```

## 🚀 快速开始

### 1. 环境准备

克隆本项目到本地：
```bash
git clone https://github.com/your-username/poetry-annotator.git
cd poetry-annotator
```

安装所需的Python依赖包：
```bash
# 核心依赖
pip install click tqdm tenacity pybreaker httpx

# LLM服务依赖
pip install google-generativeai

# 增强的JSON解析依赖 (可选但推荐)
pip install demjson3 json5
```

### 2. 项目配置

首次使用时，需要创建并编辑配置文件：

1.  复制配置文件模板：
    ```bash
    cp config/config.ini.template config/config.ini
    ```

2.  编辑 `config/config.ini` 文件，至少完成以下操作：
    *   **配置模型**: 在 `[Model.your-model-alias]` 部分，填入你的LLM提供商（`provider`）、模型名称（`model_name`）、API密钥（`api_key`）和基础URL（`base_url`）。你可以参考 `poetry-annotator.md` 示例文件。
    *   **检查路径**: 确认 `[Data]`、`[Database]` 等部分的路径设置符合你的环境。

### 3. 数据初始化

将你的原始诗词JSON数据文件（如 `ci.song.*.json`, `author.song.json`）放入 `data/source_json/` 目录。然后运行数据库初始化脚本：

```bash
python init_database.py
```
或使用CLI命令：
```bash
python src/main.py setup --init-db --clear-existing
```
该命令会读取JSON文件，创建或清空 `poetry.db` 数据库，并将诗词和作者信息存入。

### 4. 运行标注任务

#### a) 使用命令行 (CLI)

1.  **列出已配置的模型**：
    ```bash
    python src/main.py list-models
    ```

2.  **启动标注任务**：
    假设你在配置文件中定义了一个名为 `gemini-pro` 的模型：
    ```bash
    # 为 gemini-pro 模型标注前100首诗词
    python src/main.py annotate --model gemini-pro --limit 100

    # 同时为多个模型分配任务，并强制重跑
    python src/main.py annotate --model gemini-pro --model qwen-long --force-rerun
    ```

3.  **查看标注状态**：
    ```bash
    python src/main.py status
    ```

4.  **导出结果**：
    ```bash
    # 导出所有模型的标注结果
    python src/main.py export --output data/output/all_results.jsonl

    # 只导出 gemini-pro 模型的结果
    python src/main.py export --model gemini-pro
    ```

#### b) 使用图形界面 (GUI)

对于复杂的批量任务，推荐使用图形界面，它提供了更直观的操作方式。

```bash
python gui_launcher.py
```

- **任务分发 (Distribution) 选项卡**:
  - 用于运行 `distribute_tasks.py` 脚本。
  - 你可以指定模型、ID来源（单个文件或整个目录）、批次大小等，进行大规模自动化标注。
  - GUI界面的设置会自动保存，方便下次使用。

- **随机抽样 (Sampling) 选项卡**:
  - 用于运行 `random_sample.py` 脚本。
  - 你可以从数据库中随机抽取指定数量的诗词ID，并保存到一个或多个文本文件中，这些文件可用于“任务分发”。

## 📖 高级用法

### 任务分发 (`distribute_tasks.py`)

这是为大规模标注设计的核心脚本。它支持多层并发：
1.  **模型间并发**: `max_model_pipelines` 控制同时运行多少个独立的“模型-ID文件”任务。
2.  **模型内并发**: `max_workers` 控制单个模型任务内部的并发请求数。

**使用场景：**

- **场景1**: 使用 **2个模型** 分别标注 **2个不同** 的ID文件集。
  ```bash
  # 假设 id_files/ 目录下有 a.txt 和 b.txt
  # models_to_run 列表会与 id_files_in_dir 列表按顺序配对
  python distribute_tasks.py --model model_A --model model_B --id-dir data/id_files/
  ```

- **场景2**: 使用 **所有配置好的模型** 共同处理 **同一个** ID文件。
  ```bash
  python distribute_tasks.py --all-models --id-file data/ids/sample_1000.txt
  ```

- **断点续传**:
  脚本默认启用断点续传。如果任务中断，只需重新运行相同的命令，它会自动从上次失败的批次开始。若想强制从头开始，请添加 `--fresh-start` 标志。

### 情感分类体系

情感分类的规则和类别定义在 `config/中国古典诗词情感分类体系.md` 文件中。LLM会基于此文件内容进行标注。

- **格式**:
  - `####` (H4) 用于定义一级情感类别。
  - `-` (无序列表) 用于定义二级情感类别。
- **自定义**: 你可以直接修改此`md`文件来调整情感分类体系。`LabelParser`会在程序启动时自动解析并生成XML缓存以提高后续运行效率。

---

### config.ini

```ini
# Poetry Annotator 示例配置文件
#
# 这是 poetry-annotator 项目的示例配置文件 (`config.ini`)。
# 请将此内容复制到 `config/config.ini`，并根据您的实际情况修改。
#
# - 使用 `#` 或 `;` 对配置项进行注释。
# - 布尔值可以是 `True`, `False`, `yes`, `no`, `1`, `0`。
# - 路径建议使用相对路径或绝对路径。

[LLM]
# --- 并发与容错控制 ---
# 模型内最大并发工作线程数（控制单个Annotator实例的并发请求数）
max_workers = 10
# 模型间最大并发管道数（控制distribute_tasks.py同时运行多少个模型任务）
max_model_pipelines = 2
# 单次API调用失败后的最大重试次数
max_retries = 3
# 重试时的基础等待时间乘数（秒），将用于指数退避策略
retry_delay = 1
# 熔断器：在连续多少次失败后开启熔断
breaker_fail_max = 5
# 熔断器：熔断开启后，多少秒后进入半开状态尝试恢复
breaker_reset_timeout = 60

[Database]
# SQLite数据库文件路径
db_path = poetry.db

[Data]
# 存放原始JSON数据文件的目录
source_dir = data/source_json
# 存放导出结果的目录
output_dir = data/output

[Logging]
# --- 日志系统配置 ---
# 控制台显示的最低日志级别 (DEBUG, INFO, WARNING, ERROR)
console_log_level = INFO
# 文件记录的最低日志级别，建议设为DEBUG以捕获所有详细信息
file_log_level = DEBUG
# 是否启用文件日志
enable_file_log = True
# 日志文件路径，如果留空，将自动在 `logs/` 目录下创建带时间戳的文件
log_file = logs/poetry_annotator.log
# 是否启用控制台日志
enable_console_log = True
# 日志文件轮转前的最大大小（MB）
max_file_size = 10
# 保留的旧日志文件数量
backup_count = 5
# 是否静音第三方库（如httpx, urllib3）的冗余日志
quiet_third_party = True

[Categories]
# --- 情感分类体系配置 ---
# 情感分类体系的Markdown源文件路径
md_path = config/中国古典诗词情感分类体系.md
# （自动生成）情感体系的XML缓存文件路径
xml_path = config/emotion_categories.xml

[Prompt]
# --- 全局默认提示词模板路径 ---
# 这些路径可以被每个[Model.*]配置中的同名键覆盖
# 系统提示-指令部分模板
system_prompt_instruction_template = config/system_prompt_instruction.txt
# 系统提示-示例部分模板
system_prompt_example_template = config/system_prompt_example.txt
# 用户提示模板
user_prompt_template = config/user_prompt_template.txt


# ==============================================================================
# = 模型配置示例 (Model.*) =
# ==============================================================================
#
# 您可以添加任意多个 [Model.*] 配置节，`*` 部分是您为该配置起的别名。
# 这个别名将用于CLI和GUI中，例如：`python src/main.py annotate --model gemini-1.5-pro`

[Model.gemini-1.5-pro]
# 服务提供商 (目前支持: gemini, siliconflow)
provider = gemini
# 在API请求中使用的具体模型名称
model_name = models/gemini-1.5-pro-latest
# 您的API密钥
api_key = your_gemini_api_key_here
# API的基础URL (Gemini服务通常不需要配置此项，SDK会自动处理)
base_url =
# 每秒请求数 (QPS) 限制，留空或为0则不限制
rate_limit_qps = 5
# --- Gemini特定参数 ---
temperature = 0.3
max_tokens = 8192
timeout = 120
top_p = 1.0
top_k = 40
# 停止序列，用逗号分隔
stop_sequences =
# [可选] Gemini 2.5 Pro 特有参数，模型的思考时间预算（秒）
thinking_budget =

[Model.qwen-long]
# 服务提供商 (SiliconFlow兼容OpenAI API)
provider = siliconflow
# 在API请求中使用的具体模型名称
model_name = Qwen/Qwen2-7B-Instruct
# 您的API密钥
api_key = your_siliconflow_api_key_here
# API服务的基础URL
base_url = https://api.siliconflow.cn/v1/chat/completions
# 每秒请求数 (QPS) 限制
rate_limit_qps = 10
# --- SiliconFlow/OpenAI特定参数 ---
temperature = 0.1
max_tokens = 4096
timeout = 60
top_p = 0.9
# 停止序列，用逗号分隔
stop = ]
# 响应格式，对于需要JSON输出的模型，配置为 '{"type": "json_object"}'
response_format = {"type": "json_object"}
# [可选] 为模型指定一个随机种子以获得可复现的结果
seed = 12345

[Model.deepseek-v2]
# 这是另一个SiliconFlow/OpenAI兼容模型的示例
provider = siliconflow
model_name = deepseek-ai/DeepSeek-V2-Chat
api_key = your_deepseek_api_key_here
base_url = https://api.deepseek.com/v1/chat/completions
rate_limit_qps = 8
temperature = 0.2
max_tokens = 4096
timeout = 90
response_format = {"type": "json_object"}
# --- 模型特定的提示词模板 ---
# 假设这个模型需要不同的提示词，可以在这里覆盖全局配置
system_prompt_instruction_template = config/prompts_for_deepseek/system_instruction.txt
system_prompt_example_template = config/prompts_for_deepseek/system_example.txt
user_prompt_template = config/prompts_for_deepseek/user_prompt.txt

[Model.ollama-qwen]
# 这是一个通过本地Ollama服务运行模型的示例
# provider仍然是siliconflow，因为它兼容OpenAI的API格式
provider = siliconflow
model_name = qwen:7b-chat-v1.5-q4_K_M
# Ollama本地服务通常不需要API密钥，但该字段不能为空，可以填任意值
api_key = ollama
# 指向你的本地Ollama服务地址
base_url = http://localhost:11434/v1/chat/completions
# 本地服务通常没有严格的QPS限制
rate_limit_qps =
temperature = 0.2
max_tokens = 2048
timeout = 180
# [重要] Ollama的响应格式与标准OpenAI API略有不同，
# 此适配器将帮助解析Ollama特有的响应结构（例如包含<think>标签时）。
response_adapter = ollama
```
