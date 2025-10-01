"""
数据格式化模块

本模块提供将内部数据结构格式化为GUI界面可直接使用的格式的函数。
"""

from typing import Dict, Any, List

# 定义SentenceAnnotation类型，从gui_logic.py移入
# 用于存储单句标注信息的内部表示
# {
#     "sentence_id": "S1",
#     "sentence_text": "近重阳、偏多风雨，绝怜此日暄明。",
#     "primary_emotion": {"id": "01.05", "name": "01.05 愉悦"},
#     "secondary_emotions": [{"id": "01.01", "name": "01.01 喜悦"}, ...]
# }
SentenceAnnotation = Dict[str, Any]


def format_poem_info_for_display(poem_info: Dict[str, Any]) -> Dict[str, str]:
    """
    将诗词信息字典格式化为适合在GUI标签上显示的键值对。

    :param poem_info: 由 query_poem_and_annotation 返回的 poem_info 字典。
    :return: 一个字典，键为显示标签，值为对应的文本内容。
    """
    if not poem_info:
        return {}

    return {
        "标题": poem_info.get('title', '未知'),
        "作者": poem_info.get('author', '未知'),
        # full_text 通常由只读文本框直接显示，无需进一步格式化
    }


def format_sentence_annotations_for_table(sentence_annotations: List[SentenceAnnotation]) -> \
        List[Dict[str, str]]:
    """
    将句子标注列表格式化为适合在GUI表格(Treeview)中显示的数据。

    :param sentence_annotations: 由 query_poem_and_annotation 返回的 sentence_annotations 列表。
    :return: 一个字典列表，每个字典代表表格中的一行。
    """
    if not sentence_annotations:
        return []

    table_data = []
    for ann in sentence_annotations:
        # 格式化次情感列表为字符串
        secondary_names = [e['name'] for e in ann['secondary_emotions']]
        primary_display = ann['primary_emotion']['name'] if ann['primary_emotion'] else 'N/A'
        secondary_names = [e['name'] for e in ann['secondary_emotions']]
        secondary_display = ', '.join(secondary_names) if secondary_names else '无'

        table_data.append({
            "句子ID": ann['sentence_id'],
            "句子文本": ann['sentence_text'],
            "主情感": primary_display,
            "次情感": secondary_display,
            "理由": ann.get('rationale', '无')
        })

    return table_data
