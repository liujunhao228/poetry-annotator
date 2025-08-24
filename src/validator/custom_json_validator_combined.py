"""
增强型自定义JSON校验器，用于根据YAML配置文件校验LLM返回的JSON数组。
此模块支持通过配置文件定义多种校验规则集，并允许动态切换激活的规则集。
同时支持全局规则配置和项目规则配置。
兼容旧版本的API接口。
"""

import yaml
import re
from typing import Any, Dict, List, Union, Optional
from pathlib import Path


class CustomValidationError(Exception):
    """自定义校验异常类，用于表示校验失败的情况。"""
    pass


class CustomJSONValidator:
    """
    根据YAML配置文件校验JSON数组。

    Attributes:
        global_config_path (Path): 全局YAML配置文件的路径。
        project_config_path (Optional[Path]): 项目YAML配置文件的路径（可选）。
        global_config (Dict[str, Any]): 加载并解析后的全局完整配置字典。
        project_config (Optional[Dict[str, Any]]): 加载并解析后的项目完整配置字典。
        rulesets (Dict[str, Any]): 所有可用的校验规则集（全局+项目）。
        active_ruleset_name (str): 当前激活的规则集名称。
        active_ruleset (Dict[str, Any]): 当前激活的规则集配置。
    """

    def __init__(self, global_config_path: Union[str, Path],
                 project_config_path: Optional[Union[str, Path]] = None):
        """
        初始化校验器，加载配置文件。

        Args:
            global_config_path: 全局YAML配置文件的路径。
            project_config_path: 项目YAML配置文件的路径（可选）。
        """
        self.global_config_path = Path(global_config_path)
        self.project_config_path = Path(project_config_path) if project_config_path else None
        self.global_config: Dict[str, Any] = {}
        self.project_config: Optional[Dict[str, Any]] = None
        self.rulesets: Dict[str, Any] = {}
        self.active_ruleset_name: Optional[str] = None
        self.active_ruleset: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载并解析YAML配置文件。"""
        # 加载全局配置
        try:
            with open(self.global_config_path, 'r', encoding='utf-8') as f:
                self.global_config = yaml.safe_load(f)

            if not isinstance(self.global_config, dict) or 'rulesets' not in self.global_config:
                raise CustomValidationError("全局配置文件格式错误：缺少 'rulesets' 键。")

            self.rulesets.update(self.global_config.get('rulesets', {}))
            global_active_ruleset = self.global_config.get('global', {}).get('active_ruleset', None)

        except FileNotFoundError:
            raise CustomValidationError(f"全局配置文件未找到: {self.global_config_path}")
        except yaml.YAMLError as e:
            raise CustomValidationError(f"解析全局YAML配置文件时出错: {e}")

        # 加载项目配置（如果提供了路径）
        if self.project_config_path and self.project_config_path.exists():
            try:
                with open(self.project_config_path, 'r', encoding='utf-8') as f:
                    self.project_config = yaml.safe_load(f)

                if not isinstance(self.project_config, dict):
                    raise CustomValidationError("项目配置文件格式错误。")

                # 项目规则集可以覆盖全局规则集
                self.rulesets.update(self.project_config.get('rulesets', {}))
                project_active_ruleset = self.project_config.get('global', {}).get('active_ruleset', None)

            except FileNotFoundError:
                print(f"警告: 项目配置文件未找到: {self.project_config_path}")
                project_active_ruleset = None
            except yaml.YAMLError as e:
                raise CustomValidationError(f"解析项目YAML配置文件时出错: {e}")
        else:
            project_active_ruleset = None

        # 确定激活的规则集
        # 优先级: 项目配置 > 全局配置 > 默认第一个规则集
        self.active_ruleset_name = project_active_ruleset or global_active_ruleset

        if not self.active_ruleset_name:
            # 如果没有配置激活的规则集，则默认使用第一个可用的规则集
            if self.rulesets:
                self.active_ruleset_name = next(iter(self.rulesets))
                print(f"警告: 未指定 'global.active_ruleset'，将默认使用第一个规则集 '{self.active_ruleset_name}'。")
            else:
                raise CustomValidationError("配置文件格式错误：未指定 'global.active_ruleset' 且没有可用的规则集。")

        if self.active_ruleset_name not in self.rulesets:
            raise CustomValidationError(
                f"配置文件错误：指定的激活规则集 '{self.active_ruleset_name}' 不存在。"
            )

        self.active_ruleset = self.rulesets[self.active_ruleset_name]

    def reload_config(self):
        """
        重新加载配置文件。
        这在配置文件被外部修改后非常有用。
        """
        self._load_config()

    def set_active_ruleset(self, ruleset_name: str):
        """
        动态设置当前激活的规则集。

        Args:
            ruleset_name: 要激活的规则集名称。

        Raises:
            CustomValidationError: 如果指定的规则集不存在。
        """
        if ruleset_name not in self.rulesets:
            raise CustomValidationError(f"规则集 '{ruleset_name}' 不存在。")
        self.active_ruleset_name = ruleset_name
        self.active_ruleset = self.rulesets[ruleset_name]
        print(f"已切换到规则集: '{self.active_ruleset_name}'")

    def _validate_value(self, value: Any, schema: Dict[str, Any], path: str = "") -> None:
        """
        根据单个字段的schema递归校验值。

        Args:
            value: 要校验的值。
            schema: 该字段的校验规则（schema）。
            path: 当前校验的字段路径，用于错误信息。

        Raises:
            CustomValidationError: 如果校验失败。
        """
        expected_type_str = schema.get('type')
        required = schema.get('required', False)

        # 1. 检查必需字段
        if required and value is None:
            raise CustomValidationError(f"字段 '{path}' 是必需的，但缺失或为null。")

        if value is None and not required:
            return  # 非必需字段为None，校验通过

        # 2. 类型映射和检查
        type_mapping = {
            "string": str,
            "number": (int, float),
            "array": list,
            "object": dict,
            "boolean": bool
        }
        expected_type = type_mapping.get(expected_type_str)
        if not expected_type:
            raise CustomValidationError(f"配置错误：不支持的类型 '{expected_type_str}' 在字段 '{path}'。")

        if not isinstance(value, expected_type):
            raise CustomValidationError(
                f"字段 '{path}' 类型不匹配。期望 '{expected_type_str}'，实际为 '{type(value).__name__}'。"
            )

        # 3. 特定类型的额外约束
        if expected_type_str == "string":
            max_len = schema.get('max_length')
            if max_len is not None and len(value) > max_len:
                raise CustomValidationError(
                    f"字段 '{path}' 字符串长度超过限制。最大长度 {max_len}，实际长度 {len(value)}。"
                )

            min_len = schema.get('min_length')
            if min_len is not None and len(value) < min_len:
                raise CustomValidationError(
                    f"字段 '{path}' 字符串长度不足。最小长度 {min_len}，实际长度 {len(value)}。"
                )

            pattern = schema.get('pattern')
            if pattern and not re.match(pattern, value):
                raise CustomValidationError(
                    f"字段 '{path}' 不匹配正则表达式 '{pattern}'。"
                )

        elif expected_type_str == "number":
            minimum = schema.get('minimum')
            if minimum is not None and value < minimum:
                raise CustomValidationError(
                    f"字段 '{path}' 数值小于最小值。最小值 {minimum}，实际值 {value}。"
                )

            maximum = schema.get('maximum')
            if maximum is not None and value > maximum:
                raise CustomValidationError(
                    f"字段 '{path}' 数值大于最大值。最大值 {maximum}，实际值 {value}。"
                )

        elif expected_type_str == "array":
            items_schema = schema.get('items', {})
            for i, item in enumerate(value):
                self._validate_value(item, items_schema, f"{path}[{i}]")

        elif expected_type_str == "object":
            properties_schema = schema.get('properties', {})
            for key, prop_schema in properties_schema.items():
                prop_value = value.get(key)
                self._validate_value(prop_value, prop_schema, f"{path}.{key}")

            # 检查是否有不允许的额外字段
            additional_properties = schema.get('additionalProperties', True)
            if not additional_properties:
                for key in value.keys():
                    if key not in properties_schema:
                        raise CustomValidationError(
                            f"字段 '{path}' 包含未在schema中定义的额外字段 '{key}'。"
                        )

    def validate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        校验整个JSON数组。

        Args:
            data: 由LLM返回并已解析为Python对象的JSON数组。

        Returns:
            List[Dict[str, Any]]: 如果校验通过，返回原始数据。

        Raises:
            CustomValidationError: 如果校验失败。
        """
        if not isinstance(data, list):
            raise CustomValidationError("输入数据必须是一个列表。")

        item_schema = self.active_ruleset.get('item_schema')
        if not item_schema:
            raise CustomValidationError(
                f"配置错误：激活的规则集 '{self.active_ruleset_name}' 中缺少 'item_schema'。"
            )

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise CustomValidationError(f"数组中第 {i} 个元素必须是一个对象（字典）。")

            # 校验每个字段
            for field_name, field_schema in item_schema.items():
                field_value = item.get(field_name)
                self._validate_value(field_value, field_schema, f"[{i}].{field_name}")

            # 检查是否有未在schema中定义的额外字段（可选）
            # for key in item.keys():
            #     if key not in item_schema:
            #         print(f"警告：数组中第 {i} 个元素包含未在schema中定义的字段 '{key}'。")

        return data

    # --- 旧版本API兼容接口 ---

    def __init__(self, config_path: Union[str, Path]):
        """
        初始化校验器，加载配置文件。（旧版本兼容接口）

        Args:
            config_path: YAML配置文件的路径。
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.rulesets: Dict[str, Any] = {}
        self.active_ruleset_name: Optional[str] = None
        self.active_ruleset: Dict[str, Any] = {}
        self._load_config_old()

    def _load_config_old(self):
        """加载并解析YAML配置文件。（旧版本兼容接口）"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            if not isinstance(self.config, dict) or 'rulesets' not in self.config:
                raise CustomValidationError("配置文件格式错误：缺少 'rulesets' 键。")

            self.rulesets = self.config.get('rulesets', {})
            self.active_ruleset_name = self.config.get('global', {}).get('active_ruleset', None)

            if not self.active_ruleset_name:
                # 如果没有配置激活的规则集，则默认使用第一个可用的规则集
                if self.rulesets:
                    self.active_ruleset_name = next(iter(self.rulesets))
                    print(f"警告: 未指定 'global.active_ruleset'，将默认使用第一个规则集 '{self.active_ruleset_name}'。")
                else:
                    raise CustomValidationError("配置文件格式错误：未指定 'global.active_ruleset' 且没有可用的规则集。")

            if self.active_ruleset_name not in self.rulesets:
                raise CustomValidationError(
                    f"配置文件错误：指定的激活规则集 '{self.active_ruleset_name}' 不存在。"
                )

            self.active_ruleset = self.rulesets[self.active_ruleset_name]

        except FileNotFoundError:
            raise CustomValidationError(f"配置文件未找到: {self.config_path}")
        except yaml.YAMLError as e:
            raise CustomValidationError(f"解析YAML配置文件时出错: {e}")