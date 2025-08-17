# 源代码模块说明

本文档详细说明了 `src` 目录下各个模块的功能和实现细节。

## 目录结构

```
src/
├── annotation_data_logger.py
├── annotator.py
├── config_manager.py
├── data_manager.py
├── db_adapter.py
├── extract_sample_data.py
├── label_parser.py
├── llm_factory.py
├── llm_response_parser.py
├── logging_config.py
├── main.py
├── __init__.py
├── llm_services/
│   ├── __init__.py
│   ├── base_service.py
│   ├── gemini_service.py
│   └── siliconflow_service.py
└── utils/
    ├── health_checker.py
    └── rate_limiter.py
```

## 模块详细说明

### annotation_data_logger.py

**功能**: 标注数据集合日志器，用于记录即将保存的标注数据。

**主要类**:
- `AnnotationDataLogger`: 负责记录标注数据到专门的日志文件中，便于后续分析和恢复。

**关键方法**:
- `_setup_logger()`: 设置专门用于记录标注数据的logger。
- `log_annotation_data()`: 记录即将保存的标注数据（单行格式，便于机器解析）。

### annotator.py

**功能**: 诗词情感标注器，负责单个模型的并发标注任务。

**主要类**:
- `Annotator`: 实现诗词情感标注的核心逻辑，包括与LLM服务的交互、重试机制、熔断器等。

**关键方法**:
- `_generate_sentences_with_id()`: 为句子生成ID并构建JSON格式。
- `_validate_and_transform_response()`: 验证LLM响应与输入的一致性，并将其转换为最终存储格式。
- `_annotate_single_poem()`: 标注单首诗词，包含完整的处理流程和重试逻辑。
- `run()`: 异步运行指定模型的所有标注任务。

### config_manager.py

**功能**: 配置管理器，负责加载、管理和保存配置文件。

**主要类**:
- `ConfigManager`: 提供对配置文件的统一管理接口。

**关键方法**:
- `_load_config()`: 加载配置文件。
- `save_config()`: 将当前配置写入文件。
- `get_llm_config()`: 获取LLM相关配置。
- `get_model_config()`: 获取指定模型配置别名的详细配置。
- `get_database_config()`: 获取数据库配置。
- `get_data_config()`: 获取数据路径配置。

### data_manager.py

**功能**: 数据管理器，负责数据库操作和数据预处理。

**主要类**:
- `DataManager`: 提供对数据库的统一操作接口，包括诗词和作者数据的加载、标注结果的保存等。

**关键方法**:
- `_init_database()`: 初始化数据库表结构。
- `load_data_from_json()`: 从JSON文件加载数据。
- `batch_insert_poems()`: 批量插入诗词到数据库。
- `get_poems_to_annotate()`: 获取指定模型待标注的诗词。
- `save_annotation()`: 保存标注结果到annotations表。
- `get_statistics()`: 获取数据库统计信息。

### db_adapter.py

**功能**: 数据库适配器，用于支持多种数据库。

**主要类**:
- `DatabaseAdapter`: 数据库适配器抽象基类。
- `SQLiteAdapter`: SQLite数据库适配器的具体实现。

**关键方法**:
- `connect()`: 建立数据库连接。
- `init_database()`: 初始化数据库表结构。
- `execute_query()`: 执行查询操作。
- `execute_update()`: 执行更新操作。

### extract_sample_data.py

**功能**: 从数据库中提取每个表的一条示例记录并保存到文件。

**主要函数**:
- `get_sample_data()`: 执行数据库查询，提取示例数据并保存为JSON文件。

### label_parser.py

**功能**: Markdown情感体系解析器，支持从Markdown文件解析并生成XML配置。

**主要类**:
- `LabelParser`: 解析情感分类体系的Markdown文件，并提供访问接口。

**关键方法**:
- `_load_categories()`: 加载情感分类体系。
- `_parse_markdown_and_generate_xml()`: 从Markdown文件解析并生成XML。
- `get_categories_text()`: 获取格式化的情感分类文本，用于提示词。
- `validate_emotion()`: 验证情感标签是否在分类体系中。

### llm_factory.py

**功能**: LLM服务工厂，用于创建和管理不同的LLM服务实例。

**主要类**:
- `LLMFactory`: 根据配置创建不同提供商的LLM服务实例。

**关键方法**:
- `get_llm_service()`: 根据模型配置别名创建LLM服务实例。
- `list_configured_models()`: 列出在config.ini中所有已配置的模型。
- `get_service_info()`: 获取服务信息。

### llm_response_parser.py

**功能**: 针对不支持JSON输出的模型进行健壮解析。

**主要类**:
- `LLMResponseParser`: 从LLM返回的文本中解析出结构化的JSON数据。

**关键方法**:
- `parse()`: 从字符串中稳健地解析出经过内容验证的JSON数组。
- `_validate_annotation_list_content()`: 验证标注列表的内容。

### logging_config.py

**功能**: 日志配置模块，提供灵活的日志配置选项。

**主要类**:
- `LoggingConfig`: 日志配置管理器。

**关键方法**:
- `setup_logging()`: 设置日志配置。
- `_quiet_third_party_loggers()`: 静音第三方库的日志。

### main.py

**功能**: 主程序入口，提供命令行接口。

**主要功能**:
- `setup`: 初始化项目环境。
- `annotate`: 启动一个或多个模型的并发标注任务。
- `status`: 显示标注进度统计。
- `export`: 导出标注结果。
- `list-models`: 列出在config.ini中已配置的模型。
- `recover-from-logs`: 从日志文件中恢复因意外中断而未保存的标注数据。

### llm_services/ 模块

#### base_service.py

**功能**: LLM服务的基类定义。

**主要类**:
- `BaseLLMService`: 所有LLM服务的抽象基类。

#### gemini_service.py

**功能**: Google Gemini LLM服务的具体实现。

**主要类**:
- `GeminiService`: 实现与Google Gemini API的交互。

#### siliconflow_service.py

**功能**: SiliconFlow LLM服务的具体实现。

**主要类**:
- `SiliconFlowService`: 实现与SiliconFlow API的交互。

### utils/ 模块

#### health_checker.py

**功能**: 负责执行全面的任务前健康检查。

**主要类**:
- `HealthChecker`: 执行各种健康检查，包括共享资源和模型服务的检查。

**关键方法**:
- `run_all_checks()`: 执行所有必要的健康检查。
- `_check_shared_resources()`: 检查所有任务共享的资源，如配置文件、路径等。
- `_check_models()`: 并发检查指定的模型服务。
- `_check_single_model()`: 检查单个模型的配置和服务连通性。

#### rate_limiter.py

**功能**: 实现异步令牌桶速率限制器。

**主要类**:
- `AsyncTokenBucket`: 一个简单的异步令牌桶速率限制器，用于控制API调用频率。

**关键方法**:
- `__init__()`: 初始化令牌桶。
- `_refill()`: 根据流逝的时间补充令牌。
- `acquire()`: 获取一个或多个令牌，如果令牌不足则异步等待。
