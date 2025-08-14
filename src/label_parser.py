import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
import html
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging


class LabelParser:
    """Markdown情感体系解析器，支持从Markdown文件解析并生成XML配置"""
    
    def __init__(self, xml_path: Optional[str] = None, md_path: Optional[str] = None):
        """
        初始化标签解析器
        
        Args:
            xml_path: XML文件路径（可选，用于本地程序处理关系映射）
            md_path: Markdown文件路径（可选，用于LLM提示词）
        """
        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 从配置管理器获取路径，如果未提供的话
        if xml_path is None or md_path is None:
            # 延迟导入以避免循环导入
            from .config_manager import config_manager
            categories_config = config_manager.get_categories_config()
            self.xml_path = xml_path or categories_config.get('xml_path', 'config/emotion_categories.xml')
            self.md_path = md_path or categories_config.get('md_path', 'config/中国古典诗词情感分类体系.md')
        else:
            self.xml_path = xml_path
            self.md_path = md_path
            
        self.categories = OrderedDict()
        self._load_categories()
    
    def get_markdown_content(self) -> str:
        """
        直接获取 markdown 文件内容，用于 LLM 提示词
        移除"完整情感类别映射表"部分以节约token
        
        Returns:
            markdown 文件的内容（移除映射表部分）
            
        Raises:
            FileNotFoundError: 当 markdown 文件不存在时
        """
        md_file_path = Path(self.md_path)
        
        if not md_file_path.exists():
            raise FileNotFoundError(f"Markdown 文件不存在: {self.md_path}")
        
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"成功读取 Markdown 文件: {self.md_path}")
            self.logger.debug(f"原始文件大小: {len(content)} 字符")
            
            # 移除"完整情感类别映射表"及其之后的内容
            mapping_table_start = content.find('### **完整情感类别映射表**')
            if mapping_table_start != -1:
                content = content[:mapping_table_start].rstrip()
                self.logger.debug(f"移除映射表后文件大小: {len(content)} 字符")
                self.logger.info("已移除'完整情感类别映射表'部分以节约token")
            else:
                self.logger.info("未找到映射表，返回完整内容")
            
            return content
            
        except Exception as e:
            self.logger.error(f"读取 Markdown 文件失败: {e}")
            raise Exception(f"读取 Markdown 文件失败: {e}")
    
    def _load_categories(self):
        """加载情感分类体系"""
        if Path(self.xml_path).exists():
            # 如果XML文件存在，直接解析
            self._parse_xml()
        elif Path(self.md_path).exists():
            # 如果Markdown文件存在，解析并生成XML
            self._parse_markdown_and_generate_xml()
        else:
            # 如果都不存在，抛出错误
            raise FileNotFoundError(f"情感分类体系文件不存在。请确保以下文件之一存在：\n- {self.xml_path}\n- {self.md_path}")
    
    def _parse_markdown_and_generate_xml(self):
        """从Markdown文件解析并生成XML"""
        self.logger.info(f"开始解析Markdown文件: {self.md_path}")
        
        try:
            with open(self.md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 解析Markdown内容
            self._parse_markdown_content(md_content)
            
            # 生成XML文件
            self._generate_xml()
            
            self.logger.info(f"成功生成XML文件: {self.xml_path}")
            
        except Exception as e:
            self.logger.error(f"解析Markdown文件失败: {e}")
            raise FileNotFoundError(f"无法解析Markdown文件 {self.md_path}，请检查文件格式是否正确")
    
    def _parse_markdown_content(self, md_content: str):
        """解析 Markdown 内容（正则已调整）"""
        current_primary = None
        primary_count = 0
        secondary_count = 0

        self.logger.info("开始解析 Markdown 内容...")

        # 1) 一级类别：兼容 #### 01. XXX 或 #### **01. XXX**
        primary_pattern = re.compile(
            r'^#{4}\s*(?:\*\*)?(\d{2})\.\s*(.+?)(?:\*\*)?\s*(?:\(.+?\))?\s*$',
            re.UNICODE
        )

        # 2) 二级类别：兼容  - **01.01 XXX** 或 - **01.01 XXX（例：...）**
        secondary_pattern = re.compile(
            r'^\s*-\s*\*\*(\d{2}\.\d{2})\s+([^*（]+?)(?:\([^)]*\))?\*\*',
            re.UNICODE
        )

        for line_num, line in enumerate(md_content.splitlines(), 1):
            # 匹配一级类别
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
                self.logger.debug(f"找到一级类别 [{line_num}]: ID={primary_id}, 名称={primary_name}")
                continue

            # 匹配二级类别
            secondary_match = secondary_pattern.match(line)
            if secondary_match and current_primary:
                secondary_id = secondary_match.group(1)
                secondary_name = secondary_match.group(2).strip()
                current_primary['secondaries'].append({
                    'id': secondary_id,
                    'name_zh': secondary_name
                })
                secondary_count += 1
                self.logger.debug(f"  找到二级类别 [{line_num}]: ID={secondary_id}, 名称={secondary_name}")

        self.logger.info(f"\n解析完成: 共找到 {primary_count} 个一级类别, {secondary_count} 个二级类别")

        # 解析映射表以获取英文名称
        self._parse_mapping_table(md_content)
    
    def _parse_mapping_table(self, md_content: str):
        """解析映射表以获取英文名称"""
        mapping_dict = {}
        in_mapping_table = False
        mapping_count = 0
        
        self.logger.info("\n开始解析映射表...")
        
        for line_num, line in enumerate(md_content.split('\n'), 1):
            if '### **完整情感类别映射表**' in line:
                in_mapping_table = True
                self.logger.debug(f"找到映射表起始位置 [{line_num}]")
                continue
            
            if in_mapping_table and line.startswith('|'):
                # 跳过表头和分隔线
                if '---' in line or '字段命名' in line or not line.strip():
                    continue
                
                # 提取映射关系
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    chinese_key = parts[0].strip()
                    english_value = parts[1].strip().strip('"')
                    
                    # 添加到映射字典
                    mapping_dict[chinese_key] = english_value
                    mapping_count += 1
                    self.logger.debug(f"  映射条目 [{line_num}]: '{chinese_key}' -> '{english_value}'")
        
        self.logger.info(f"映射表解析完成: 共找到 {mapping_count} 个映射条目")
        
        # 将映射信息添加到类别数据
        self._apply_mapping_to_categories(mapping_dict)
    
    def _apply_mapping_to_categories(self, mapping_dict: Dict[str, str]):
        """将映射信息应用到类别数据"""
        unmatched_primary = 0
        unmatched_secondary = 0
        
        self.logger.info("\n开始匹配中英文名称...")
        
        for primary_id, primary in self.categories.items():
            # 查找一级类别的英文名称
            primary_key_full = f"{primary_id}. {primary['name_zh']}"
            primary_key_id = f"{primary_id}."
            
            if primary_key_full in mapping_dict:
                primary['name_en'] = mapping_dict[primary_key_full]
                self.logger.debug(f"  一级匹配成功: {primary_key_full} -> {primary['name_en']}")
            else:
                # 尝试匹配ID开头的键
                matched = False
                for key in mapping_dict:
                    if key.startswith(primary_key_id):
                        primary['name_en'] = mapping_dict[key]
                        matched = True
                        self.logger.debug(f"  一级ID匹配: {key} -> {primary['name_en']}")
                        break
                
                if not matched:
                    primary['name_en'] = ""
                    unmatched_primary += 1
                    self.logger.warning(f"  ⚠️ 一级未匹配: {primary_key_full}")
            
            for secondary in primary['secondaries']:
                # 查找二级类别的英文名称
                secondary_key_full = f"{secondary['id']} {secondary['name_zh']}"
                secondary_key_id = secondary['id']
                
                if secondary_key_full in mapping_dict:
                    secondary['name_en'] = mapping_dict[secondary_key_full]
                    self.logger.debug(f"    二级匹配成功: {secondary_key_full} -> {secondary['name_en']}")
                else:
                    # 尝试匹配ID开头的键
                    matched = False
                    for key in mapping_dict:
                        if key.startswith(secondary_key_id):
                            secondary['name_en'] = mapping_dict[key]
                            matched = True
                            self.logger.debug(f"    二级ID匹配: {key} -> {secondary['name_en']}")
                            break
                    
                    if not matched:
                        secondary['name_en'] = ""
                        unmatched_secondary += 1
                        self.logger.warning(f"    ⚠️ 二级未匹配: {secondary_key_full}")
        
        self.logger.info(f"\n匹配完成: 一级未匹配数={unmatched_primary}, 二级未匹配数={unmatched_secondary}")
    
    def _generate_xml(self):
        """生成XML文件"""
        self.logger.info("\n开始构建XML结构...")
        root = ET.Element("EmotionCategories")
        
        # 添加一级和二级类别
        for primary_id, primary_data in self.categories.items():
            # 转义XML特殊字符
            name_zh = html.escape(primary_data['name_zh'])
            name_en = html.escape(primary_data.get('name_en', ''))
            
            primary_elem = ET.SubElement(
                root, 
                "PrimaryCategory",
                id=primary_data['id'],
                name_zh=name_zh,
                name_en=name_en
            )
            self.logger.debug(f"添加一级类别: {primary_data['id']} - {name_zh}")
            
            for secondary in primary_data['secondaries']:
                # 转义XML特殊字符
                sec_name_zh = html.escape(secondary['name_zh'])
                sec_name_en = html.escape(secondary.get('name_en', ''))
                
                ET.SubElement(
                    primary_elem, 
                    "SecondaryCategory",
                    id=secondary['id'],
                    name_zh=sec_name_zh,
                    name_en=sec_name_en
                )
                self.logger.debug(f"  添加二级类别: {secondary['id']} - {sec_name_zh}")
        
        self.logger.info("XML结构构建完成")
        
        # 美化XML输出
        self._indent_xml(root)
        
        # 写入XML文件
        Path(self.xml_path).parent.mkdir(parents=True, exist_ok=True)
        tree = ET.ElementTree(root)
        tree.write(self.xml_path, 
                   encoding='utf-8', 
                   xml_declaration=True,
                   short_empty_elements=False)
    
    def _indent_xml(self, elem, level=0):
        """美化XML格式"""
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def _parse_xml(self):
        """解析现有的XML文件"""
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
            
            self.logger.info(f"成功解析XML文件: 共找到 {len(self.categories)} 个一级类别")
            
        except Exception as e:
            self.logger.error(f"解析XML文件失败: {e}")
            raise FileNotFoundError(f"无法解析XML文件 {self.xml_path}，请检查文件格式是否正确")
    

    
    def get_categories_text(self) -> str:
        """获取格式化的情感分类文本，用于提示词"""
        # 优先使用 markdown 文件内容
        try:
            return self.get_markdown_content()
        except Exception as e:
            self.logger.warning(f"无法读取 Markdown 文件，回退到 XML 解析: {e}")
            # 回退到原有的 XML 解析方式
            return self._get_categories_text_from_xml()
    
    def _get_categories_text_from_xml(self) -> str:
        """从 XML 解析获取格式化的情感分类文本（回退方法）"""
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
        """获取所有情感分类ID和名称的映射"""
        categories = {}
        for primary_data in self.categories.values():
            categories[primary_data['id']] = primary_data['name_zh']
            for secondary in primary_data['secondaries']:
                categories[secondary['id']] = secondary['name_zh']
        return categories
    
    def validate_emotion(self, emotion: str) -> bool:
        """验证情感标签是否在分类体系中"""
        all_categories = self.get_all_categories()
        return emotion in all_categories
    
    def get_primary_category(self, secondary_id: str) -> Optional[str]:
        """根据二级类别ID获取一级类别ID"""
        for primary_id, primary_data in self.categories.items():
            for secondary in primary_data['secondaries']:
                if secondary['id'] == secondary_id:
                    return primary_id
        return None


# 全局标签解析器实例
label_parser = LabelParser()  # 使用默认配置，从 config_manager 获取路径