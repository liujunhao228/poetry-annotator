"""
情感标签解析器 - 从 Markdown/XML 文件解析情感分类体系
"""

import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
import html
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging


class LabelParser:
    """Markdown 情感体系解析器"""

    def __init__(self, xml_path: Optional[str] = None, md_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        self.xml_path = xml_path or 'config/emotion_categories.xml'
        self.md_path = md_path or 'config/中国古典诗词情感分类体系.md'

        self.categories = OrderedDict()
        self._load_categories()

    def get_markdown_content(self) -> str:
        """获取 markdown 文件内容，用于 LLM 提示词"""
        md_file_path = Path(self.md_path)

        if not md_file_path.exists():
            raise FileNotFoundError(f"Markdown 文件不存在：{self.md_path}")

        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            mapping_table_start = content.find('### **完整情感类别映射表**')
            if mapping_table_start != -1:
                content = content[:mapping_table_start].rstrip()

            return content

        except Exception as e:
            self.logger.error(f"读取 Markdown 文件失败：{e}")
            raise

    def _load_categories(self):
        """加载情感分类体系"""
        if Path(self.xml_path).exists():
            self._parse_xml()
        elif Path(self.md_path).exists():
            self._parse_markdown_and_generate_xml()
        else:
            raise FileNotFoundError(f"情感分类体系文件不存在：\n- {self.xml_path}\n- {self.md_path}")

    def _parse_markdown_and_generate_xml(self):
        """从 Markdown 文件解析并生成 XML"""
        try:
            with open(self.md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            self._parse_markdown_content(md_content)
            self._generate_xml()
        except Exception as e:
            self.logger.error(f"解析 Markdown 文件失败：{e}")
            raise

    def _parse_markdown_content(self, md_content: str):
        """解析 Markdown 内容"""
        current_primary = None
        primary_count = 0
        secondary_count = 0

        primary_pattern = re.compile(
            r'^#{4}\s*(?:\*\*)?(\d{2})\.\s*(.+?)(?:\*\*)?\s*(?:\(.+?\))?\s*$',
            re.UNICODE
        )

        secondary_pattern = re.compile(
            r'^\s*-\s*\*\*(\d{2}\.\d{2})\s+([^*（]+?)(?:\([^)]*\))?\*\*',
            re.UNICODE
        )

        for line in md_content.splitlines():
            primary_match = primary_pattern.match(line)
            if primary_match:
                primary_id = primary_match.group(1)
                primary_name = primary_match.group(2).strip()
                current_primary = {
                    'id': primary_id,
                    'name_zh': primary_name,
                    'secondaries': []
                }
                self.categories[primary_id] = current_primary
                primary_count += 1
                continue

            secondary_match = secondary_pattern.match(line)
            if secondary_match and current_primary:
                secondary_id = secondary_match.group(1)
                secondary_name = secondary_match.group(2).strip()
                current_primary['secondaries'].append({
                    'id': secondary_id,
                    'name_zh': secondary_name
                })
                secondary_count += 1

        self._parse_mapping_table(md_content)

    def _parse_mapping_table(self, md_content: str):
        """解析映射表以获取英文名称"""
        mapping_dict = {}
        in_mapping_table = False

        for line in md_content.split('\n'):
            if '### **完整情感类别映射表**' in line:
                in_mapping_table = True
                continue

            if in_mapping_table and line.startswith('|'):
                if '---' in line or '字段命名' in line or not line.strip():
                    continue

                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    chinese_key = parts[0].strip()
                    english_value = parts[1].strip().strip('"')
                    mapping_dict[chinese_key] = english_value

        self._apply_mapping_to_categories(mapping_dict)

    def _apply_mapping_to_categories(self, mapping_dict: Dict[str, str]):
        """将映射信息应用到类别数据"""
        for primary_id, primary in self.categories.items():
            primary_key_full = f"{primary_id}. {primary['name_zh']}"
            primary_key_id = f"{primary_id}."

            if primary_key_full in mapping_dict:
                primary['name_en'] = mapping_dict[primary_key_full]
            else:
                matched = False
                for key in mapping_dict:
                    if key.startswith(primary_key_id):
                        primary['name_en'] = mapping_dict[key]
                        matched = True
                        break
                if not matched:
                    primary['name_en'] = ""

            for secondary in primary['secondaries']:
                secondary_key_full = f"{secondary['id']} {secondary['name_zh']}"
                secondary_key_id = secondary['id']

                if secondary_key_full in mapping_dict:
                    secondary['name_en'] = mapping_dict[secondary_key_full]
                else:
                    matched = False
                    for key in mapping_dict:
                        if key.startswith(secondary_key_id):
                            secondary['name_en'] = mapping_dict[key]
                            matched = True
                            break
                    if not matched:
                        secondary['name_en'] = ""

    def _generate_xml(self):
        """生成 XML 文件"""
        root = ET.Element("EmotionCategories")

        for primary_id, primary_data in self.categories.items():
            name_zh = html.escape(primary_data['name_zh'])
            name_en = html.escape(primary_data.get('name_en', ''))

            primary_elem = ET.SubElement(
                root, "PrimaryCategory",
                id=primary_data['id'], name_zh=name_zh, name_en=name_en
            )

            for secondary in primary_data['secondaries']:
                sec_name_zh = html.escape(secondary['name_zh'])
                sec_name_en = html.escape(secondary.get('name_en', ''))
                ET.SubElement(
                    primary_elem, "SecondaryCategory",
                    id=secondary['id'], name_zh=sec_name_zh, name_en=sec_name_en
                )

        self._indent_xml(root)

        Path(self.xml_path).parent.mkdir(parents=True, exist_ok=True)
        tree = ET.ElementTree(root)
        tree.write(self.xml_path, encoding='utf-8', xml_declaration=True, short_empty_elements=False)

    def _indent_xml(self, elem, level=0):
        """美化 XML 格式"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def _parse_xml(self):
        """解析现有的 XML 文件"""
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()

            for primary_elem in root.findall('PrimaryCategory'):
                primary_id = primary_elem.get('id')
                primary_name_zh = primary_elem.get('name_zh')
                primary_name_en = primary_elem.get('name_en', '')

                primary_data = {
                    'id': primary_id,
                    'name_zh': primary_name_zh,
                    'name_en': primary_name_en,
                    'secondaries': []
                }

                for secondary_elem in primary_elem.findall('SecondaryCategory'):
                    secondary_id = secondary_elem.get('id')
                    secondary_name_zh = secondary_elem.get('name_zh')
                    secondary_name_en = secondary_elem.get('name_en', '')

                    primary_data['secondaries'].append({
                        'id': secondary_id,
                        'name_zh': secondary_name_zh,
                        'name_en': secondary_name_en
                    })

                self.categories[primary_id] = primary_data

        except Exception as e:
            self.logger.error(f"解析 XML 文件失败：{e}")
            raise

    def get_categories_text(self) -> str:
        """获取格式化的情感分类文本，用于提示词"""
        try:
            return self.get_markdown_content()
        except Exception:
            return self._get_categories_text_from_xml()

    def _get_categories_text_from_xml(self) -> str:
        """从 XML 解析获取格式化的情感分类文本"""
        text = "## 情感分类体系：\n\n"
        for primary_id, primary_data in self.categories.items():
            text += f"**{primary_id}. {primary_data['name_zh']}** ({primary_data.get('name_en', '')})\n"
            for secondary in primary_data['secondaries']:
                text += f"- **{secondary['id']} {secondary['name_zh']}** ({secondary.get('name_en', '')})\n"
            text += "\n"
        return text

    def get_all_categories(self) -> List[str]:
        """获取所有情感分类名称"""
        categories = []
        for primary_data in self.categories.values():
            categories.append(primary_data['name_zh'])
            categories.extend([sec['name_zh'] for sec in primary_data['secondaries']])
        return categories

    def get_all_categories_with_ids(self) -> Dict[str, str]:
        """获取所有情感分类 ID 和名称的映射"""
        categories = {}
        for primary_data in self.categories.values():
            categories[primary_data['id']] = primary_data['name_zh']
            for secondary in primary_data['secondaries']:
                categories[secondary['id']] = secondary['name_zh']
        return categories

    def validate_emotion(self, emotion: str) -> bool:
        """验证情感标签是否在分类体系中"""
        return emotion in self.get_all_categories()

    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """根据二级类别 ID 获取一级类别 ID"""
        for primary_id, primary_data in self.categories.items():
            for secondary in primary_data['secondaries']:
                if secondary['id'] == secondary_id:
                    return primary_id
        return None
