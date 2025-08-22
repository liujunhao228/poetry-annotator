"""
预处理分类规则管理器，用于加载和管理预处理分类规则。
支持全局规则配置和项目规则配置。
"""

import yaml
from typing import Any, Dict, List, Union, Optional
from pathlib import Path


class PreprocessingRuleError(Exception):
    """预处理规则异常类，用于表示规则加载或应用失败的情况。"""
    pass


class PreprocessingRuleManager:
    """
    预处理分类规则管理器。

    Attributes:
        global_config_path (Path): 全局YAML配置文件的路径。
        project_config_path (Optional[Path]): 项目YAML配置文件的路径（可选）。
        global_config (Dict[str, Any]): 加载并解析后的全局完整配置字典。
        project_config (Optional[Dict[str, Any]]): 加载并解析后的项目完整配置字典。
        rules (Dict[str, Any]): 所有可用的预处理规则（全局+项目）。
        global_settings (Dict[str, Any]): 全局设置。
    """

    def __init__(self, global_config_path: Union[str, Path],
                 project_config_path: Optional[Union[str, Path]] = None):
        """
        初始化预处理规则管理器，加载配置文件。

        Args:
            global_config_path: 全局YAML配置文件的路径。
            project_config_path: 项目YAML配置文件的路径（可选）。
        """
        self.global_config_path = Path(global_config_path)
        self.project_config_path = Path(project_config_path) if project_config_path else None
        self.global_config: Dict[str, Any] = {}
        self.project_config: Optional[Dict[str, Any]] = None
        self.rules: Dict[str, Any] = {}
        self.global_settings: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载并解析YAML配置文件。"""
        # 加载全局配置
        try:
            with open(self.global_config_path, 'r', encoding='utf-8') as f:
                self.global_config = yaml.safe_load(f)

            if not isinstance(self.global_config, dict) or 'rules' not in self.global_config:
                raise PreprocessingRuleError("全局配置文件格式错误：缺少 'rules' 键。")

            self.rules.update(self.global_config.get('rules', {}))
            self.global_settings.update(self.global_config.get('global_settings', {}))

        except FileNotFoundError:
            raise PreprocessingRuleError(f"全局配置文件未找到: {self.global_config_path}")
        except yaml.YAMLError as e:
            raise PreprocessingRuleError(f"解析全局YAML配置文件时出错: {e}")

        # 加载项目配置（如果提供了路径）
        if self.project_config_path and self.project_config_path.exists():
            try:
                with open(self.project_config_path, 'r', encoding='utf-8') as f:
                    self.project_config = yaml.safe_load(f)

                if not isinstance(self.project_config, dict):
                    raise PreprocessingRuleError("项目配置文件格式错误。")

                # 项目规则可以覆盖全局规则
                self.rules.update(self.project_config.get('rules', {}))
                self.global_settings.update(self.project_config.get('global_settings', {}))

            except FileNotFoundError:
                print(f"警告: 项目配置文件未找到: {self.project_config_path}")
            except yaml.YAMLError as e:
                raise PreprocessingRuleError(f"解析项目YAML配置文件时出错: {e}")

    def reload_config(self):
        """
        重新加载配置文件。
        这在配置文件被外部修改后非常有用。
        """
        self._load_config()

    def get_rules(self) -> Dict[str, Any]:
        """
        获取所有预处理规则。

        Returns:
            Dict[str, Any]: 所有预处理规则。
        """
        return self.rules

    def get_global_settings(self) -> Dict[str, Any]:
        """
        获取全局设置。

        Returns:
            Dict[str, Any]: 全局设置。
        """
        return self.global_settings

    def apply_rules(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用预处理规则到数据。

        Args:
            data: 要应用规则的数据列表。

        Returns:
            List[Dict[str, Any]]: 应用规则后的数据。
        """
        # 这里只是一个示例实现，实际的规则应用逻辑可能会更复杂
        # 需要根据具体的规则定义来实现
        for item in data:
            # 应用每条规则
            for rule_name, rule_config in self.rules.items():
                if not rule_config.get('enabled', True):
                    continue

                keywords = rule_config.get('keywords', [])
                fields = rule_config.get('fields', self.global_settings.get('default_check_fields', []))
                category = rule_config.get('category')

                # 检查字段中是否包含关键词
                match = False
                for field in fields:
                    field_value = item.get(field, "")
                    if isinstance(field_value, str):
                        for keyword in keywords:
                            if keyword in field_value:
                                match = True
                                break
                    if match:
                        break

                # 如果匹配，更新分类字段
                if match and category:
                    classification_field = self.global_settings.get('classification_field', 'pre_classification')
                    item[classification_field] = category

        return data