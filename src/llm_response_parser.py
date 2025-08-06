"""
针对不支持JSON输出的模型进行健壮解析
"""

import json
import re
from typing import Any, List, Dict, Optional

class LLMResponseParser:
    """
    一个健壮的LLM响应解析器，能够从包含额外文本或Markdown代码块的字符串中提取一个JSON数组。
    此解析器集成了内容验证逻辑，确保返回的数组不仅格式正确，而且内容也符合业务规范。
    """

    def _validate_annotation_list_content(self, result_list: list) -> List[Dict[str, Any]]:
        """
        [新增] 验证标注列表的内容。这是从 BaseLLMService 迁移过来的核心验证逻辑。
        如果验证失败，它会抛出 ValueError 或 TypeError。
        """
        if not result_list:
            raise ValueError("解析成功，但JSON数组为空")
        
        if not isinstance(result_list, list):
            raise TypeError(f"期望得到列表，但实际类型是 {type(result_list)}")

        for i, item in enumerate(result_list):
            if not isinstance(item, dict):
                raise ValueError(f"列表第 {i+1} 项不是字典格式: {item}")
            
            # 验证必需字段
            required_fields = ['id', 'primary', 'secondary']
            for field in required_fields:
                if field not in item:
                    raise ValueError(f"列表第 {i+1} 项缺少必要字段: '{field}' in {item}")
            
            # 验证字段类型
            if not isinstance(item['id'], str) or not item['id']:
                raise TypeError(f"列表第 {i+1} 项的 'id' 字段必须是非空字符串: {item['id']}")
            
            if not isinstance(item['primary'], str) or not item['primary']:
                raise TypeError(f"列表第 {i+1} 项的 'primary' 字段必须是非空字符串: {item['primary']}")
            
            if not isinstance(item['secondary'], list):
                raise TypeError(f"列表第 {i+1} 项的 'secondary' 字段必须是列表: {type(item['secondary'])}")
            
            # 验证secondary列表中的每个元素都是字符串
            for j, secondary_id in enumerate(item['secondary']):
                if not isinstance(secondary_id, str):
                    raise TypeError(f"列表第 {i+1} 项 'secondary' 字段中的第 {j+1} 个元素必须是字符串: {secondary_id}")
        
        # 验证通过，直接返回原始列表
        return result_list

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        从字符串中稳健地解析出经过内容验证的JSON数组。

        处理策略:
        1. 尝试从Markdown代码块 (```json ... ```) 中提取并进行“解析+验证”。
        2. 如果失败，尝试从整个文本中提取第一个出现的、完整的JSON数组 (`[...]`) 并进行“解析+验证”。
        3. 如果失败，尝试从整个文本中提取第一个出现的、完整的JSON对象 (`{...}`)，并查找其中符合规范的数组。
        4. 如果失败，尝试在文本中查找所有独立的JSON对象，将它们聚合成一个数组后进行“解析+验证”。
        5. 如果所有策略都失败，则抛出异常。
        
        任何一个步骤中的“验证失败”都会被捕获，并允许解析器继续尝试下一个策略。

        Args:
            text: LLM返回的原始文本。

        Returns:
            一个经过完全验证的、包含标注信息的字典列表。

        Raises:
            ValueError: 如果所有策略都无法解析出有效的、且内容符合业务规范的JSON数组。
        """
        if not isinstance(text, str):
            raise TypeError(f"输入必须是字符串, 而不是 {type(text)}")

        text = text.strip()
        
        # [修改] 每个 try 块现在都捕获所有解析和验证的错误，以便继续下一个策略
        
        # 策略 1: 查找Markdown格式的JSON代码块
        markdown_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if markdown_match:
            json_str = markdown_match.group(1).strip()
            try:
                return self._parse_and_validate_structure(json_str)
            except (ValueError, TypeError, json.JSONDecodeError):
                # 如果代码块内容解析或验证失败，使用其内容继续尝试其他策略
                text_to_parse = json_str
            else:
                text_to_parse = text
        else:
            text_to_parse = text

        # 策略 2: 提取第一个完整的JSON数组 `[...]`
        array_match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', text_to_parse)
        if array_match:
            try:
                return self._parse_and_validate_structure(array_match.group(0))
            except (ValueError, TypeError, json.JSONDecodeError):
                pass # 解析或验证失败，继续

        # 策略 3: 提取第一个完整的JSON对象 `{...}` 并查找内部数组
        object_match = re.search(r'\{\s*[\s\S]*?\s*\}', text_to_parse)
        if object_match:
            try:
                return self._parse_and_validate_structure(object_match.group(0))
            except (ValueError, TypeError, json.JSONDecodeError):
                pass # 解析或验证失败，继续

        # 策略 4: 查找所有独立的JSON对象，修复并组合成一个列表
        try:
            individual_objects_str = re.findall(r'(\{[\s\S]*?\})(?=\s*\{|\s*$)', text_to_parse, re.DOTALL)
            if individual_objects_str:
                parsed_objects = []
                for obj_str in individual_objects_str:
                    try:
                        cleaned_obj_str = obj_str.strip()
                        if cleaned_obj_str.endswith(','):
                            cleaned_obj_str = cleaned_obj_str[:-1]
                        
                        data = json.loads(cleaned_obj_str)
                        # 仅添加字典，以防解析出非字典内容
                        if isinstance(data, dict):
                           parsed_objects.append(data)
                           
                    except json.JSONDecodeError:
                        continue # 忽略无法解析的片段
                
                if parsed_objects:
                    # 对聚合后的列表进行一次完整的验证
                    return self._validate_annotation_list_content(parsed_objects)

        except (ValueError, TypeError, json.JSONDecodeError):
            pass  # 聚合或验证失败，继续最后的尝试

        # 最后手段：尝试直接解析整个文本
        try:
            return self._parse_and_validate_structure(text_to_parse)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise ValueError(f"所有策略均无法从响应中解析出有效的、内容合规的JSON数组。最终错误: {e}") from e

    def _parse_and_validate_structure(self, json_str: str) -> List[Dict[str, Any]]:
        """
        [修改] 解析字符串，并立即对其内容进行深度验证。
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解码失败: {e}") from e

        # Case 1: 结果直接就是目标数组，对其进行内容验证
        if isinstance(data, list):
            return self._validate_annotation_list_content(data)

        # Case 2: 结果是一个对象，查找其中可能包含的目标数组
        if isinstance(data, dict):
            # 常见的包裹键: 'annotations', 'result', 'data', 'choices'
            for key in ['annotations', 'result', 'data', 'choices']:
                if key in data and isinstance(data[key], list):
                    try:
                        # 对找到的列表进行内容验证
                        return self._validate_annotation_list_content(data[key])
                    except (ValueError, TypeError):
                        continue # 此列表内容不合规，继续查找下一个
            # 查找第一个值为列表的键
            for value in data.values():
                if isinstance(value, list):
                    try:
                        # 对找到的列表进行内容验证
                        return self._validate_annotation_list_content(value)
                    except (ValueError, TypeError):
                        continue # 此列表内容不合规，继续查找下一个

        raise ValueError(f"解析后的数据既不是合规的字典列表，也不是包含合规字典列表的对象。数据类型: {type(data)}")


# 创建一个全局单例，方便在其他模块中直接使用
llm_response_parser = LLMResponseParser()
