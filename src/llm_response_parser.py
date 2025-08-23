"""
针对不支持JSON输出的模型进行健壮解析
"""

from abc import ABC, abstractmethod
import json
import re
from typing import Any, List, Dict, Optional
from pathlib import Path

# 可选依赖：demjson3 和 json5
try:
    import demjson3 as demjson
except ImportError:
    demjson = None # 如果未安装，优雅地处理
try:
    import json5
except ImportError:
    json5 = None # 如果未安装，优雅地处理

class ILLMResponseParser(ABC):
    """LLM响应解析器接口"""
    
    @abstractmethod
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        从字符串中解析出经过内容验证的JSON数组。
        Args:
            text: LLM返回的原始文本。
        Returns:
            一个经过完全验证的、包含标注信息的字典列表。
        Raises:
            ValueError, TypeError: 如果解析或验证失败。
        """
        pass

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
            
            # 自动去除ID首尾空格
            if 'id' in item and isinstance(item['id'], str):
                item['id'] = item['id'].strip()
                            
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

    def _pre_process_and_fix_json(self, s: str) -> str:
        """
        [新增] 在解析前对JSON字符串进行清理和修复，提高解析成功率。
        """
        # 1. 移除模型可能添加的解释性前缀，例如 "Here is the JSON output:"
        s = re.sub(r'^\s*.*?[\:\[\{]', '', s, 1) if not s.lstrip().startswith(('[', '{')) else s
        s = s.strip()
        # 2. 替换非标准的Unicode引号
        s = s.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
        # 3. 移除各类注释
        s = re.sub(r'//.*', '', s)  # 移除 // 行注释
        s = re.sub(r'/\*[\s\S]*?\*/', '', s, flags=re.MULTILINE) # 移除 /* */ 块注释
        # 4. 修复悬尾逗号 (trailing commas)
        s = re.sub(r',\s*([\}\]])', r'\1', s)
        
        # 5. 尝试修复对象间缺失的逗号
        s = re.sub(r'\}\s*\{', '}, {', s)
        # 6. 将Python风格的布尔/None值转为JSON标准
        s = re.sub(r'\bTrue\b', 'true', s)
        s = re.sub(r'\bFalse\b', 'false', s)
        s = re.sub(r'\bNone\b', 'null', s)
        return s

    def _try_parse_with_multiple_libs(self, json_str: str) -> Any:
        """
        [新增] 按顺序使用多个解析库尝试解析字符串，从最严格到最宽容。
        """
        processed_str = self._pre_process_and_fix_json(json_str)
        
        # 策略 1: 标准库 json (最快, 最严格)
        try:
            return json.loads(processed_str)
        except json.JSONDecodeError:
            pass
        # 策略 2: json5 (处理注释, 单引号, 悬尾逗号等)
        if json5:
            try:
                return json5.loads(processed_str)
            except Exception: # json5 异常类型不统一
                pass
        else:
            # 如果未安装，可以记录一个警告
            # logger.warning("json5 library not installed. Skipping.")
            pass
        # 策略 3: demjson (非常宽容，作为最后手段)
        if demjson:
            try:
                return demjson.decode(processed_str)
            except demjson.JSONDecodeError:
                pass
        else:
            # logger.warning("demjson3 library not installed. Skipping.")
            pass
        # 如果所有库都失败了
        raise ValueError("所有解析库都无法解析该字符串。")

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
        [已增强] 使用多库解析器和预处理来解析字符串，并立即对其内容进行深度验证。
        """
        try:
            # 核心改动：用我们强大的新函数替换了原始的 json.loads
            data = self._try_parse_with_multiple_libs(json_str)
        except ValueError as e:
            # _try_parse_with_multiple_libs 抛出的异常已经很清晰了
            raise ValueError(f"JSON解码失败，已尝试多种修复和解析策略。原始错误: {e}") from e

        # Case 1: 结果直接就是目标数组，对其进行内容验证
        if isinstance(data, list):
            return self._validate_annotation_list_content(data)

        # Case 2: 结果是一个对象，查找其中可能包含的目标数组
        if isinstance(data, dict):
            # 常见的包裹键: 'annotations', 'result', 'data', 'choices'
            for key in ['annotations', 'result', 'data', 'choices']:
                if key in data and isinstance(data[key], list):
                    try:
                        return self._validate_annotation_list_content(data[key])
                    except (ValueError, TypeError):
                        continue
            # 查找第一个值为列表的键
            for value in data.values():
                if isinstance(value, list):
                    try:
                        return self._validate_annotation_list_content(value)
                    except (ValueError, TypeError):
                        continue

        raise ValueError(f"解析后的数据既不是合规的字典列表，也不是包含合规字典列表的对象。数据类型: {type(data)}")



# 创建一个全局单例，方便在其他模块中直接使用
llm_response_parser = LLMResponseParser()
