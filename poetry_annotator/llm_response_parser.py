"""
LLM 响应解析器 - 健壮的 JSON 解析和内容验证
"""

import json
import re
from typing import Any, List, Dict, Optional

# 可选依赖
try:
    import demjson3 as demjson
except ImportError:
    demjson = None

try:
    import json5
except ImportError:
    json5 = None


class LLMResponseParser:
    """健壮的 LLM 响应解析器"""

    def _validate_annotation_list_content(self, result_list: list) -> List[Dict[str, Any]]:
        """验证标注列表的内容"""
        if not result_list:
            raise ValueError("解析成功，但 JSON 数组为空")

        if not isinstance(result_list, list):
            raise TypeError(f"期望得到列表，但实际类型是 {type(result_list)}")

        for i, item in enumerate(result_list):
            if not isinstance(item, dict):
                raise ValueError(f"列表第 {i+1} 项不是字典格式：{item}")

            if 'id' in item and isinstance(item['id'], str):
                item['id'] = item['id'].strip()

            required_fields = ['id', 'primary', 'secondary']
            for field in required_fields:
                if field not in item:
                    raise ValueError(f"列表第 {i+1} 项缺少必要字段：'{field}' in {item}")

            if not isinstance(item['id'], str) or not item['id']:
                raise TypeError(f"列表第 {i+1} 项的 'id' 字段必须是非空字符串：{item['id']}")

            if not isinstance(item['primary'], str) or not item['primary']:
                raise TypeError(f"列表第 {i+1} 项的 'primary' 字段必须是非空字符串：{item['primary']}")

            if not isinstance(item['secondary'], list):
                raise TypeError(f"列表第 {i+1} 项的 'secondary' 字段必须是列表：{type(item['secondary'])}")

            for j, secondary_id in enumerate(item['secondary']):
                if not isinstance(secondary_id, str):
                    raise TypeError(f"列表第 {i+1} 项 'secondary' 字段中的第 {j+1} 个元素必须是字符串：{secondary_id}")

        return result_list

    def _pre_process_and_fix_json(self, s: str) -> str:
        """在解析前对 JSON 字符串进行清理和修复"""
        s = re.sub(r'^\s*.*?[\:\[\{]', '', s, 1) if not s.lstrip().startswith(('[', '{')) else s
        s = s.strip()
        s = s.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")
        s = re.sub(r'//.*', '', s)
        s = re.sub(r'/\*[\s\S]*?\*/', '', s, flags=re.MULTILINE)
        s = re.sub(r',\s*([\}\]])', r'\1', s)
        s = re.sub(r'\}\s*\{', '}, {', s)
        s = re.sub(r'\bTrue\b', 'true', s)
        s = re.sub(r'\bFalse\b', 'false', s)
        s = re.sub(r'\bNone\b', 'null', s)
        return s

    def _try_parse_with_multiple_libs(self, json_str: str) -> Any:
        """使用多个解析库尝试解析字符串"""
        processed_str = self._pre_process_and_fix_json(json_str)

        try:
            return json.loads(processed_str)
        except json.JSONDecodeError:
            pass

        if json5:
            try:
                return json5.loads(processed_str)
            except Exception:
                pass

        if demjson:
            try:
                return demjson.decode(processed_str)
            except demjson.JSONDecodeError:
                pass

        raise ValueError("所有解析库都无法解析该字符串。")

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """从字符串中稳健地解析出 JSON 数组"""
        if not isinstance(text, str):
            raise TypeError(f"输入必须是字符串，而不是 {type(text)}")

        text = text.strip()

        markdown_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if markdown_match:
            json_str = markdown_match.group(1).strip()
            try:
                return self._parse_and_validate_structure(json_str)
            except (ValueError, TypeError, json.JSONDecodeError):
                text_to_parse = json_str
            else:
                text_to_parse = text
        else:
            text_to_parse = text

        array_match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', text_to_parse)
        if array_match:
            try:
                return self._parse_and_validate_structure(array_match.group(0))
            except (ValueError, TypeError, json.JSONDecodeError):
                pass

        object_match = re.search(r'\{\s*[\s\S]*?\s*\}', text_to_parse)
        if object_match:
            try:
                return self._parse_and_validate_structure(object_match.group(0))
            except (ValueError, TypeError, json.JSONDecodeError):
                pass

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
                        if isinstance(data, dict):
                            parsed_objects.append(data)
                    except json.JSONDecodeError:
                        continue
                if parsed_objects:
                    return self._validate_annotation_list_content(parsed_objects)
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

        try:
            return self._parse_and_validate_structure(text_to_parse)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise ValueError(f"所有策略均无法解析出有效的 JSON 数组。最终错误：{e}") from e

    def _parse_and_validate_structure(self, json_str: str) -> List[Dict[str, Any]]:
        """解析字符串并验证内容"""
        try:
            data = self._try_parse_with_multiple_libs(json_str)
        except ValueError as e:
            raise ValueError(f"JSON 解码失败：{e}") from e

        if isinstance(data, list):
            return self._validate_annotation_list_content(data)

        if isinstance(data, dict):
            for key in ['annotations', 'result', 'data', 'choices']:
                if key in data and isinstance(data[key], list):
                    try:
                        return self._validate_annotation_list_content(data[key])
                    except (ValueError, TypeError):
                        continue
            for value in data.values():
                if isinstance(value, list):
                    try:
                        return self._validate_annotation_list_content(value)
                    except (ValueError, TypeError):
                        continue

        raise ValueError(f"解析后的数据不是合规的字典列表。数据类型：{type(data)}")


llm_response_parser = LLMResponseParser()
