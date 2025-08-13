# processing_logic_refactored.py
import re
from typing import List, Dict, Tuple, Optional

class TextProcessorRefactored:
    """
    封装所有文本处理逻辑。
    此重构版本以结构化数据为核心，为表格化UI提供健壮的后端支持。
    负责：
    1.  文本 -> 结构化数据 (解析)
    2.  结构化数据 -> 文本 (生成)
    3.  数据校验
    """
    # --- 常量 ---
    MAPPING_TABLE_TITLE = "### **完整情感类别映射表**"
    MAPPING_TABLE_HEADER = "| 原始中文类目               | 字段命名 (JSON键值)             |"
    MAPPING_TABLE_SEPARATOR = "|----------------------------|----------------------------------|"

    # --- 1. 核心解析逻辑 (文本 -> 结构化数据) ---

    def extract_mapping_content(self, full_text: str) -> Tuple[str, str]:
        """从完整文本中分离出主内容和映射表Markdown。"""
        parts = full_text.split(self.MAPPING_TABLE_TITLE, 1)
        if len(parts) == 2:
            main_content = parts[0].strip()
            mapping_md = self.MAPPING_TABLE_TITLE + parts[1]
            return main_content, mapping_md
        return full_text.strip(), ""

    def parse_main_content_to_structure(self, main_content_text: str) -> List[Dict]:
        """
        【新增核心功能】将主内容文本解析为一个结构化字典列表。
        这是表格化编辑器的基础数据源。
        参考了 process5.py 的思路但进行了泛化和强化。
        """
        structure = []
        # 正则：匹配一级类别，支持可选的例句
        primary_pattern = re.compile(
            r"^#{4}\s*\*\*(?P<id>\d{2})\.\s*(?P<name>[^（\n]+?)\s*(?:（例：(?P<example>.*?)）)?\*\*$"
        )
        # 正则：匹配二级类别，支持可选的例句
        secondary_pattern = re.compile(
            r"^\s*-\s*\*\*(?P<id>\d{2}\.\d{2})\s+(?P<name>[^：\n]+?)\*\*：\s*(?P<desc>.*?)\s*(?:（例：(?P<example>.*?)）)?$"
        )
        # 正则：处理没有描述只有名称和例句的二级类别
        secondary_simple_pattern = re.compile(
            r"^\s*-\s*\*\*(?P<id>\d{2}\.\d{2})\s+(?P<name>[^（\n]+?)\s*（例：(?P<example>.*?)）\*\*$"
        )
        # 正则：处理只有名称的二级类别
        secondary_nameonly_pattern = re.compile(
             r"^\s*-\s*\*\*(?P<id>\d{2}\.\d{2})\s+(?P<name>[^：\n（]+?)\*\*$"
        )


        # 按空行分割，处理每个类别组
        groups = main_content_text.strip().split('\n\n')
        for group in groups:
            lines = [line.strip() for line in group.strip().split('\n') if line.strip()]
            if not lines:
                continue

            # 处理一级类别
            p_match = primary_pattern.match(lines[0])
            if p_match:
                data = p_match.groupdict()
                structure.append({
                    'level': 1,
                    'id': data['id'],
                    'name': data['name'].strip(),
                    'description': '', # 一级类别无描述
                    'example': (data['example'] or '').strip()
                })

                # 处理该组内的二级类别
                for line in lines[1:]:
                    s_match = secondary_pattern.match(line)
                    if s_match:
                        s_data = s_match.groupdict()
                        structure.append({
                            'level': 2,
                            'id': s_data['id'],
                            'name': s_data['name'].strip(),
                            'description': s_data['desc'].strip(),
                            'example': (s_data.get('example') or '').strip()
                        })
                        continue
                    
                    s_simple_match = secondary_simple_pattern.match(line)
                    if s_simple_match:
                        s_data = s_simple_match.groupdict()
                        structure.append({
                            'level': 2,
                            'id': s_data['id'],
                            'name': s_data['name'].strip(),
                            'description': '',
                            'example': (s_data.get('example') or '').strip()
                        })
                        continue
                    
                    s_nameonly_match = secondary_nameonly_pattern.match(line)
                    if s_nameonly_match:
                        s_data = s_nameonly_match.groupdict()
                        structure.append({
                            'level': 2,
                            'id': s_data['id'],
                            'name': s_data['name'].strip(),
                            'description': '',
                            'example': ''
                        })

        return structure

    def parse_mapping_from_md(self, mapping_md: str) -> Dict[str, str]:
        """从映射表的Markdown文本中解析出键值对字典。(与旧版类似)"""
        mappings = {}
        if not mapping_md: return mappings
        for line in mapping_md.split('\n'):
            line = line.strip()
            if line.startswith('|') and '---' not in line and '字段命名' not in line and not line.startswith('| **'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2 and re.match(r'^\d', parts[0]):
                    mappings[parts[0]] = parts[1]
        return mappings

    # --- 2. 核心生成逻辑 (结构化数据 -> 文本) ---

    @staticmethod
    def get_full_key(item: Dict) -> str:
        """根据结构化数据项生成用于映射表的唯一键。"""
        if item['level'] == 1:
            return f"{item['id']}. {item['name']}"
        else: # level 2
            return f"{item['id']} {item['name']}"

    def generate_main_content_from_structure(self, structure: List[Dict]) -> str:
        """
        【新增核心功能】根据结构化数据列表，生成格式正确的Markdown主内容。
        这替代了旧的、脆弱的 `format_for_saving` 函数。
        """
        output_lines = []
        last_level = 0
        
        primary_items = [item for item in structure if item['level'] == 1]
        
        for p_item in primary_items:
            # 添加一级类别与上一组之间的空行
            if output_lines:
                output_lines.append("")

            # 格式化一级类别行
            example_str = f"（例：{p_item['example']}）" if p_item['example'] else ""
            p_line = f"#### **{p_item['id']}. {p_item['name']}**"
            if example_str:
                p_line = f"#### **{p_item['id']}. {p_item['name']} {example_str}**"
            else:
                 p_line = f"#### **{p_item['id']}. {p_item['name']}**"
            output_lines.append(p_line)
            
            # 寻找并格式化其下的所有二级类别
            secondary_items = [
                item for item in structure 
                if item['level'] == 2 and item['id'].startswith(p_item['id'] + '.')
            ]
            for s_item in secondary_items:
                desc_str = f"：{s_item['description']}" if s_item['description'] else ""
                example_str = f"（例：{s_item['example']}）" if s_item['example'] else ""
                s_line = f"- **{s_item['id']} {s_item['name']}**{desc_str} {example_str}".strip()
                output_lines.append(s_line)

        return "\n".join(output_lines)

    def generate_mapping_md(self, structure: List[Dict], mappings: Dict[str, str]) -> str:
        """根据最新的结构化数据和映射数据，生成Markdown映射表。"""
        output_lines = [
            self.MAPPING_TABLE_TITLE, "",
            self.MAPPING_TABLE_HEADER,
            self.MAPPING_TABLE_SEPARATOR
        ]
        
        def add_section(items, title):
            if not items: return
            output_lines.append(f"| {title} | |")
            for item in sorted(items, key=lambda x: x['id']):
                key = self.get_full_key(item)
                value = mappings.get(key, "")
                output_lines.append(f"| {key.ljust(26)} | {value.ljust(32)} |")

        primary_cats = [c for c in structure if c['level'] == 1]
        secondary_cats = [c for c in structure if c['level'] == 2]

        add_section(primary_cats, "**一级类别**")
        add_section(secondary_cats, "**二级类别**")

        return "\n".join(output_lines)

    # --- 3. 校验逻辑 ---
    
    def validate_consistency(self, structure: List[Dict], mappings: Dict[str, str]) -> List[str]:
        """校验主内容结构与映射表内容是否一致。"""
        errors = []
        category_keys = {self.get_full_key(cat) for cat in structure}
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
    
    def Renumber_structure(self, structure: List[Dict]) -> List[Dict]:
        """【新增工具】对整个结构进行重新编号，保持层级关系。"""
        new_structure = []
        p_count = 0
        s_count = 0
        last_pid = ""

        for item in structure:
            new_item = item.copy()
            if new_item['level'] == 1:
                p_count += 1
                s_count = 0  # 重置二级类别计数器
                new_pid = f"{p_count:02d}"
                new_item['id'] = new_pid
                last_pid = new_pid
            elif new_item['level'] == 2:
                if not new_item['id'].startswith(last_pid):
                     s_count = 0 # 如果父ID变化，也重置
                s_count += 1
                new_item['id'] = f"{last_pid}.{s_count:02d}"

            new_structure.append(new_item)
        return new_structure
