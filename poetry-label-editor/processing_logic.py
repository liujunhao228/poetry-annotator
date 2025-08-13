# processing_logic.py

import re
from typing import List, Dict, Tuple

class TextProcessor:
    """
    封装所有用于情感标注文本的解析、校验、格式化和生成逻辑。
    此版本为重构版，支持结构化数据，并为表格化UI提供核心支持。
    """
    # --- 映射表处理常量 ---
    MAPPING_TABLE_TITLE = "### **完整情感类别映射表**"
    MAPPING_TABLE_HEADER = "| 原始中文类目               | 字段命名 (JSON键值)             |"
    MAPPING_TABLE_SEPARATOR = "|----------------------------|----------------------------------|"

    # --- 核心数据处理工作流 (New & Refactored) ---

    def extract_mapping_content(self, full_text: str) -> Tuple[str, str]:
        """
        从完整文本中分离出主内容（类别定义）和映射表部分的Markdown文本。
        
        Args:
            full_text: 完整的Markdown文件内容。
            
        Returns:
            一个元组 (主内容文本, 映射表Markdown文本)。如果未找到映射表，则第二个元素为空字符串。
        """
        parts = full_text.split(self.MAPPING_TABLE_TITLE, 1)
        if len(parts) == 2:
            main_content = parts[0].rstrip()
            mapping_md = self.MAPPING_TABLE_TITLE + parts[1]
            return main_content, mapping_md
        return full_text, ""

    def parse_categories_from_main_content(self, main_content_text: str) -> List[Dict]:
        """
        从主内容文本中解析所有一级和二级类别，返回一个结构化的字典列表。
        这是UI生成映射表表格的基础。

        Args:
            main_content_text: 只包含类别定义的主内容文本。

        Returns:
            一个字典列表，例如:
            [
                {'id': '01', 'name': '自然山水', 'full_key': '01. 自然山水', 'level': 1},
                {'id': '01.01', 'name': '山水之乐', 'full_key': '01.01 山水之乐', 'level': 2},
                ...
            ]
        """
        categories = []
        primary_pattern = re.compile(r'^#{4}\s*(?:\*\*)?(\d{2})\.\s*([^:*（\n]+)')
        secondary_pattern = re.compile(r'^\s*-\s*\*\*(\d{2}\.\d{2})\s+([^*（：\n]+)')

        for line in main_content_text.splitlines():
            clean_line = line.strip()

            p_match = primary_pattern.match(clean_line)
            if p_match:
                cat_id = p_match.group(1)
                cat_name = p_match.group(2).strip()
                categories.append({
                    'id': cat_id,
                    'name': cat_name,
                    'full_key': f"{cat_id}. {cat_name}",
                    'level': 1
                })
                continue
            
            s_match = secondary_pattern.match(clean_line)
            if s_match:
                cat_id = s_match.group(1)
                cat_name = s_match.group(2).strip()
                categories.append({
                    'id': cat_id,
                    'name': cat_name,
                    'full_key': f"{cat_id} {cat_name}",
                    'level': 2
                })
        return categories

    def parse_mapping_from_md(self, mapping_md: str) -> Dict[str, str]:
        """
        从映射表的Markdown文本中解析出键值对字典。

        Args:
            mapping_md: 包含映射表的Markdown文本。

        Returns:
            一个字典，例如: {'01. 自然山水': 'NatureLandscape', ...}
        """
        mappings = {}
        if not mapping_md:
            return mappings

        for line in mapping_md.split('\n'):
            line = line.strip()
            if line.startswith('|') and '---' not in line and '字段命名' not in line and not line.startswith('| **'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2 and re.match(r'^\d', parts[0]):
                    key = parts[0]
                    value = parts[1]
                    mappings[key] = value
        return mappings

    def validate_consistency(self, categories: List[Dict], mappings: Dict[str, str]) -> List[str]:
        """
        【核心校验】校验主内容解析出的类别与映射表内容是否一一对应。
        
        Args:
            categories: 从主内容解析出的类别字典列表。
            mappings: 从映射表解析或UI中获取的映射字典。
            
        Returns:
            一个错误信息字符串列表。如果列表为空，则表示校验通过。
        """
        errors = []
        category_keys = {cat['full_key'] for cat in categories}
        mapping_keys = set(mappings.keys())

        missing_in_mapping = sorted(list(category_keys - mapping_keys))
        if missing_in_mapping:
            for key in missing_in_mapping:
                errors.append(f"缺失映射：主内容中的类别 '{key}' 在映射表中不存在。")

        extra_in_mapping = sorted(list(mapping_keys - category_keys))
        if extra_in_mapping:
            for key in extra_in_mapping:
                errors.append(f"冗余映射：映射表中的条目 '{key}' 在主内容中已不存在。")
        
        return errors

    def generate_mapping_md(self, categories: List[Dict], mappings: Dict[str, str]) -> str:
        """
        根据最新的类别列表和映射数据，生成格式化、完整的Markdown映射表。

        Args:
            categories: 最新的类别字典列表。
            mappings: 最新的映射字典。

        Returns:
            一个字符串，包含完整的、格式正确的Markdown映射表。
        """
        output_lines = [
            self.MAPPING_TABLE_TITLE, "",
            self.MAPPING_TABLE_HEADER,
            self.MAPPING_TABLE_SEPARATOR
        ]

        def add_section_to_table(cat_list: List[Dict], heading: str):
            if not cat_list: return
            output_lines.append(f"| {heading} | |")
            for cat in sorted(cat_list, key=lambda x: x['id']):
                key = cat['full_key']
                value = mappings.get(key, "")
                output_lines.append(f"| {key.ljust(26)} | {value.ljust(32)} |")

        primary_cats = [c for c in categories if c['level'] == 1]
        secondary_cats = [c for c in categories if c['level'] == 2]

        add_section_to_table(primary_cats, "**一级类别**")
        add_section_to_table(secondary_cats, "**二级类别**")

        return "\n".join(output_lines)

    # --- UI工具栏功能 ---

    def clear_numbers(self, text: str) -> str:
        """
        【新】仅从主内容区清除行首的类别编号 (如 "01.", "01.01 ")。
        此函数非常安全，只会移除与标准格式匹配的编号，避免误删内容。
        """
        main_content, _ = self.extract_mapping_content(text)
        cleaned_lines = []

        # 正则表达式，用于匹配并捕获标准格式行中的前缀、编号和内容
        primary_pattern = re.compile(r'^(####\s*(?:\*\*)?)((\d{2})\.\s*)(.*)')
        secondary_pattern = re.compile(r'^(\s*-\s*\*\*)((\d{2}\.\d{2})\s+)(.*)')

        for line in main_content.split('\n'):
            p_match = primary_pattern.match(line)
            if p_match:
                # 重组行，但不包含编号部分
                cleaned_lines.append(f"{p_match.group(1)}{p_match.group(4)}")
                continue
            
            s_match = secondary_pattern.match(line)
            if s_match:
                # 重组行，但不包含编号部分
                cleaned_lines.append(f"{s_match.group(1)}{s_match.group(4)}")
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def clear_special_symbols(self, text: str) -> str:
        """
        【新】仅从主内容区清除Markdown格式化符号 (如 ####, **, -)。
        """
        main_content, _ = self.extract_mapping_content(text)
        cleaned_lines = []

        for line in main_content.split('\n'):
            # 移除行首的Markdown标记
            temp_line = re.sub(r'^\s*#+\s*', '', line).strip()
            temp_line = re.sub(r'^\s*-\s*', '', temp_line).strip()
            
            # 移除用于加粗的星号
            temp_line = temp_line.replace('**', '')
            
            cleaned_lines.append(temp_line)
        
        # 保持段落间的空行结构
        return '\n'.join(cleaned_lines)

    def remove_examples(self, text: str) -> str:
        """
        从主内容区移除所有全角括号及其中的内容。
        """
        main_content, _ = self.extract_mapping_content(text)
        return re.sub(r'（[^）]*）', '', main_content).strip()

    def format_for_saving(self, text_to_format: str) -> str:
        """
        【更新】将纯文本或仅有数字的文本转换为最终的MD格式。
        此函数能智能识别并保留已有的数字编号，或为无编号文本自动生成编号。
        仅处理主内容区。
        """
        groups = [group for group in text_to_format.strip().split('\n\n') if group.strip()]
        
        main_cat_num = 0
        formatted_content_lines = []

        # Regex patterns to detect existing numbering
        primary_pattern = re.compile(r'^\s*(\d{2})\.?\s*(.*)', re.DOTALL)
        secondary_pattern = re.compile(r'^\s*(\d{2}\.\d{2})\s*(.*)', re.DOTALL)

        for group in groups:
            lines = [line.strip() for line in group.split('\n') if line.strip()]
            if not lines:
                continue
            
            # --- 处理主类别 ---
            primary_line_text = lines[0]
            p_match = primary_pattern.match(primary_line_text)
            
            if p_match:
                main_cat_id = p_match.group(1)
                primary_text = p_match.group(2).strip()
                main_cat_num = int(main_cat_id) # 同步计数器
            else:
                main_cat_num += 1
                main_cat_id = f"{main_cat_num:02d}"
                primary_text = primary_line_text
            
            primary_title = f"{main_cat_id}. {primary_text}"
            formatted_content_lines.append(f"#### **{primary_title}**")
            
            # --- 处理子类别 ---
            sub_cat_num = 0
            for sub_line_text in lines[1:]:
                s_match = secondary_pattern.match(sub_line_text)
                
                if s_match:
                    sub_cat_id = s_match.group(1)
                    secondary_text = s_match.group(2).strip()
                    # 从ID中提取子类别编号，以保持计数器同步
                    try:
                        sub_cat_num = int(sub_cat_id.split('.')[1])
                    except (ValueError, IndexError):
                        pass # 如果格式不规范，则忽略
                else:
                    sub_cat_num += 1
                    sub_cat_id = f"{main_cat_id}.{sub_cat_num:02d}"
                    secondary_text = sub_line_text
                
                # 格式化子类别行
                if '：' in secondary_text:
                    sub_title, description = secondary_text.split('：', 1)
                    secondary_line = f"- **{sub_cat_id} {sub_title.strip()}**：{description.strip()}"
                else:
                    secondary_line = f"- **{sub_cat_id} {secondary_text}**"
                formatted_content_lines.append(secondary_line)
            
            # 在每个大类组之后添加一个空行，以保持格式清晰
            if formatted_content_lines:
                 formatted_content_lines.append("")

        return "\n".join(formatted_content_lines).strip()
