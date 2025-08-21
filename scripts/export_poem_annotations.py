"""
诗词标注数据导出命令行工具

该脚本提供一个命令行接口，用于导出指定诗词的所有模型标注数据，
并将其处理为包含中文情感名称的Markdown表格格式输出到控制台或文件。
"""

import argparse
import sys
import os
import logging

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 添加项目路径 ---
# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (假设脚本在项目根目录或其子目录)
project_root = script_dir
# 向上查找包含 src 目录的根目录
for _ in range(3): # 假设最多3层嵌套
    if os.path.exists(os.path.join(project_root, 'src')):
        break
    project_root = os.path.dirname(project_root)
else:
    logger.error("无法找到项目根目录 (包含 'src' 文件夹)")
    sys.exit(1)

# 将项目根目录和 data-visualizer 添加到 Python 路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

data_visualizer_path = os.path.join(project_root, 'poetry-annotator-data-visualizer')
if data_visualizer_path not in sys.path:
    sys.path.insert(0, data_visualizer_path)

# --- 导入我们的模块 ---
try:
    from src.annotation_data_exporter import AnnotationDataExporter
    import pandas as pd
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    sys.exit(1)


def dataframe_to_markdown_table(df: pd.DataFrame) -> str:
    """
    将 pandas DataFrame 转换为 Markdown 表格字符串。

    :param df: 输入的 DataFrame。
    :return: Markdown 表格字符串。
    """
    if df.empty:
        return "空表格"

    # 获取列名
    headers = df.columns.tolist()
    
    # 创建表头行
    header_row = "| " + " | ".join(headers) + " |"
    
    # 创建分隔行
    separator_row = "| " + " | ".join([":---" for _ in headers]) + " |"
    
    # 创建数据行
    data_rows = []
    for _, row in df.iterrows():
        # 将每个单元格的值转为字符串，并处理可能的换行符
        processed_row = [str(v).replace('\n', '<br>') for v in row]
        data_rows.append("| " + " | ".join(processed_row) + " |")
    
    # 组合所有行
    markdown_table = "\n".join([header_row, separator_row] + data_rows)
    return markdown_table


def main():
    """主函数，解析命令行参数并执行导出逻辑。"""
    parser = argparse.ArgumentParser(
        description="导出指定诗词的所有模型标注数据为Markdown表格。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-d', '--db_name',
        type=str,
        default="default",
        help='要查询的数据库名称 (默认: "default")。\n'
             '可用的数据库名称取决于 config.ini 中的配置。'
    )
    parser.add_argument(
        '-p', '--poem_id',
        type=int,
        required=True,
        help='要导出标注数据的诗词ID (整数)。'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出Markdown文件的路径。如果未指定，则输出到控制台。'
    )

    args = parser.parse_args()

    db_name = args.db_name
    poem_id = args.poem_id
    output_file = args.output

    logger.info(f"开始导出诗词ID {poem_id} 的标注数据 (数据库: {db_name})")

    try:
        # 1. 创建导出器实例
        exporter = AnnotationDataExporter(db_name=db_name)

        # 2. 获取标注数据DataFrame，仅包含指定列
        required_columns = ['model_identifier', 'sentence_id', 'primary_emotion_name', 'secondary_emotion_names']
        df = exporter.get_annotations_for_poem(poem_id, columns=required_columns)

        if df.empty:
            message = f"诗词ID {poem_id} 没有可用的标注数据。"
            logger.info(message)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(message + "\n")
            else:
                print(message)
            return

        # 3. 转换为Markdown表格
        markdown_table = dataframe_to_markdown_table(df)

        # 4. 输出结果
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_table)
                logger.info(f"成功导出Markdown表格到文件: {output_file}")
            except Exception as e:
                logger.error(f"写入文件 {output_file} 失败: {e}")
                sys.exit(1)
        else:
            print(markdown_table)
            logger.info("成功输出Markdown表格到控制台。")

    except Exception as e:
        logger.error(f"导出过程中发生未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()