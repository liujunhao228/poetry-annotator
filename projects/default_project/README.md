# 默认项目模板

这是一个默认的项目模板，用于 `poetry-annotator` 工具。

## 目录结构

- `config.ini`: 项目配置文件，定义了数据库路径、数据源路径、模型配置等。
- `data/`: 存放项目相关的数据文件，如诗词数据、数据库文件、分类体系文件等。
- `logs/`: 存放项目运行时生成的日志文件。

## 使用方法

1. 将此目录复制并重命名为您的项目名称。
2. 修改 `config.ini` 文件中的各项配置，特别是 API 密钥和路径设置。
3. 在 `data/` 目录下放置您的诗词 JSON 数据文件。
4. 使用命令行工具时，通过 `--project <项目名称>` 参数指定项目。

例如：
```bash
python main.py --project my_poetry_project setup --init-db
python main.py --project my_poetry_project annotate --model gpt-4o
