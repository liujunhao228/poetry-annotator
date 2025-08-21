# Scripts 目录说明

本目录包含了一系列用于诗词情感标注项目的 Python 脚本工具，每个脚本都有特定的功能，用于数据处理、任务分发、统计分析等。

## 脚本功能详细说明

### 1. annotation_statistics.py
用于统计指定数据库的诗词情感标注情况。

**主要功能：**
- 统计去重和不去重的已标注诗词数和分句数
- 按模型分类统计标注情况
- 支持输出到 CSV 文件

**使用方法：**
```bash
python annotation_statistics.py --db <数据库名称> [--output <输出文件路径>]
```

**参数说明：**
- `--db`：指定要统计的数据库名称（必需）
- `--output`：指定输出 CSV 文件路径（可选）

### 2. check_db.py
检查数据库连接和基本数据。

**主要功能：**
- 验证数据库是否正确设置
- 显示数据库中的表和样本数据

**使用方法：**
```bash
python check_db.py
```

### 3. distribute_tasks.py
任务分发工具，用于从文件读取诗词ID并分发标注任务。

**主要功能：**
- 支持多模型、高并发处理
- 支持传入单个列表文件或包含多个列表文件的目录
- 具有进度管理和断点续传功能
- 支持日志级别控制

**使用方法：**
```bash
python distribute_tasks.py --model <模型名> --id-file <ID文件路径> [其他选项]
python distribute_tasks.py --all-models --id-dir <ID目录路径> [其他选项]
```

**参数说明：**
- `--model/-m`：指定要使用的模型配置别名（与 --all-models 互斥）
- `--all-models/-a`：对所有已配置的模型执行标注任务（与 --model 互斥）
- `--id-file/-f`：包含诗词ID的文本文件路径（与 --id-dir 互斥）
- `--id-dir/-d`：包含多个诗词ID文件的目录路径（与 --id-file 互斥）
- `--force-rerun/-r`：强制重新标注已完成的条目
- `--chunk-size/-c`：每个批次处理的诗词数量（默认1000）
- `--fresh-start/-s`：忽略并清除旧的进度，从头开始运行
- `--db`：数据库名称（从配置文件中获取路径）
- `--console-log-level`：设置控制台的日志级别（覆盖配置文件）
- `--file-log-level`：设置文件日志的级别（覆盖配置文件）
- `--enable-file-log`：强制启用文件日志（覆盖配置文件）

### 4. find_duplicate_poems.py
查找数据库中 full_text 字段内容相同的诗词ID组。

**主要功能：**
- 用于发现和处理重复数据
- 支持将结果保存为 JSON 文件

**使用方法：**
```bash
python find_duplicate_poems.py [--db-path <数据库路径>] [--db-name <数据库名称>] [--output-file <输出文件>]
```

**参数说明：**
- `--db-path`：数据库文件的路径
- `--db-name`：数据库名称（从配置文件中获取路径）
- `--output-file`：将结果保存为JSON文件的路径

### 5. gui_launcher.py
图形用户界面启动器。

**主要功能：**
- 提供 Tkinter GUI 来运行其他脚本的功能
- 包含任务分发、随机抽样、日志恢复等功能的可视化界面

**详细说明：**
请参阅 [GUI_README.md](GUI_README.md) 获取完整的功能介绍和使用说明。

### 6. init_database.py
初始化数据库。

**主要功能：**
- 从 JSON 文件加载诗词数据到数据库中
- 显示数据库统计信息

**使用方法：**
```bash
python init_database.py
```

### 7. proofread_annotations.py
校对诗词标注状态。

**主要功能：**
- 检查指定ID列表中的诗词是否已成功标注
- 生成已完成和待处理的ID列表

**使用方法：**
```bash
python proofread_annotations.py --id-file <ID文件路径> --model <模型标识符> [其他选项]
```

**参数说明：**
- `--db-path`：SQLite数据库文件路径
- `--id-file`：包含待校对诗词ID的文本文件路径（每行一个ID）
- `--model`：要校对的标注模型标识符
- `--output-dir`：用于存放'已完成'和'待处理'ID列表的输出目录
- `--chunk-size`：每次从数据库查询的ID数量

### 8. random_sample.py
随机抽取诗词ID。

**主要功能：**
- 支持过滤包含缺字标记的诗词
- 支持排除已标注的诗词
- 可按ID升序排序或随机排序输出
- 支持分段输出到多个文件

**使用方法：**
```bash
python random_sample.py --count <抽样数量> [其他选项]
```

**参数说明：**
- `--db`：SQLite数据库文件路径（默认: poetry.db）
- `--db-name`：数据库名称（从配置文件中获取路径）
- `-n/--count`：要抽取的诗词ID数量（默认: 1）
- `--exclude-annotated`：启用排除已标注诗词功能
- `--model`：模型标识符，用于排除已标注诗词
- `--sort`：按ID升序排序输出到文件
- `--no-shuffle`：禁用默认的输出随机排序
- `--output-file`：指定输出文件完整路径
- `--output-dir`：指定输出文件存放的目录
- `--num-files`：指定分段输出的文件个数（默认: 1）

### 9. recover_from_log_v6.py
从日志文件中恢复因意外中断而未保存的标注数据（旧版本）。

**主要功能：**
- 适配旧的日志格式
- 支持试运行模式

**使用方法：**
```bash
python recover_from_log_v6.py --file <日志文件> --model <模型标识符> [其他选项]
python recover_from_log_v6.py --dir <日志目录> --model <模型标识符> [其他选项]
```

**参数说明：**
- `--file`：要处理的单个日志文件路径
- `--dir`：包含日志文件 (*.log) 的目录路径
- `--model`：保存标注到数据库时使用的模型标识符
- `--db-path`：手动指定数据库文件路径
- `--write`：使用此标志以实际写入数据库（默认为试运行）

### 10. recover_from_log_v7.py
从日志文件中恢复因意外中断而未保存的标注数据（新版本）。

**主要功能：**
- 适配新的单行JSON日志格式
- 模型标识符直接从日志条目中读取
- 支持试运行模式

**使用方法：**
```bash
python recover_from_log_v7.py --file <日志文件> [其他选项]
python recover_from_log_v7.py --dir <日志目录> [其他选项]
```

**参数说明：**
- `--file`：要处理的单个日志文件路径
- `--dir`：包含日志文件 (*.log) 的目录路径
- `--db-path`：手动指定数据库文件路径
- `--write`：使用此标志以实际写入数据库（默认为试运行）

### 11. data_cleaning.py
数据清洗工具，用于清洗诗词数据，标记包含缺字、空内容或其他问题的数据。

**主要功能：**
- 检测并标记包含缺字符号"□"的诗词
- 检测并标记空内容（去除标点符号后无有效文字）的诗词
- 检测并标记标题或内容中括号内含有特殊符号的"存疑"诗词
- 重置所有诗词数据状态为"active"
- 生成数据清洗报告

**使用方法：**
```bash
python data_cleaning.py --db-name <数据库名称> --clean [--dry-run]
python data_cleaning.py --db-name <数据库名称> --reset [--dry-run]
python data_cleaning.py --db-name <数据库名称> --report
```

**参数说明：**
- `--db-name`：数据库名称（从配置文件中获取）
- `--clean`：执行数据清洗操作
- `--reset`：重置所有数据状态为active
- `--report`：生成清洗报告
- `--dry-run`：试运行模式，不实际修改数据

## 使用说明

每个脚本都可以通过命令行直接运行，具体参数和使用方法请参考各脚本文件内的说明或使用 `-h` 或 `--help` 参数查看帮助信息。

例如：
```bash
python annotation_statistics.py --help
python distribute_tasks.py --help
python random_sample.py --help
```

## 注意事项

1. 运行这些脚本前，请确保已正确配置项目环境和数据库连接。
2. 部分脚本可能需要特定的命令行参数，请参考脚本内的说明。
3. 建议在运行重要操作前先使用试运行模式（如适用）确认操作的正确性。
4. 对于涉及数据库写入的操作，请特别小心，建议先备份数据库。
