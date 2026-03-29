"""配置服务 - GUI 与项目上下文的适配器"""

from pathlib import Path
from typing import Optional, Any, Dict, List

from ..models.schema_definition import ProjectSchema


class ConfigService:
    """
    GUI 配置服务 - 项目上下文的 GUI 适配器

    职责：
    1. 持有 Project 实例引用
    2. 将 Project 的能力转换为 GUI 友好的接口
    3. 提供 GUI 专用的状态管理（如缓存、变更通知）
    4. 提供项目 Schema 定义用于动态 UI 生成
    """

    def __init__(self, project: Any):
        """
        初始化配置服务

        Args:
            project: 项目上下文实例（Project 类）
        """
        self.project = project
        self._project_root = project.root_path
        self._config_manager = project.config_manager

        # GUI 专用缓存
        self._models_cache: Optional[List[str]] = None
        self._db_config_cache: Optional[Dict] = None
        self._schema_cache: Optional[ProjectSchema] = None

    # 兼容旧代码：提供 config_manager 属性
    @property
    def config_manager(self) -> Any:
        """获取配置管理器 - 直接来自 Project（兼容旧代码）"""
        return self._config_manager

    # ========== 委托给 Project 的方法 ==========

    def get_project_root(self) -> Path:
        """获取项目根目录 - 直接来自 Project"""
        return self._project_root

    def get_config_manager(self) -> Any:
        """获取配置管理器 - 直接来自 Project"""
        return self._config_manager

    def get_project_type(self) -> str:
        """获取项目类型名称"""
        return self.project.project_type

    # ========== Schema 相关方法 ==========

    def get_project_schema(self, refresh: bool = False) -> ProjectSchema:
        """
        获取项目 Schema 定义

        Args:
            refresh: 是否刷新缓存

        Returns:
            ProjectSchema 实例
        """
        if self._schema_cache is None or refresh:
            try:
                project_type = self.get_project_type()
                self._schema_cache = ProjectSchema.from_project_type(project_type)
            except Exception as e:
                print(f"错误：加载项目 Schema 失败：{e}")
                # 返回空 Schema
                self._schema_cache = ProjectSchema(
                    project_type=self.get_project_type(),
                    fields={}
                )
        return self._schema_cache

    # ========== GUI 专用适配方法 ==========

    def list_models(self, refresh: bool = False) -> List[str]:
        """
        获取已配置的模型列表

        Args:
            refresh: 是否刷新缓存

        Returns:
            模型配置名称列表
        """
        if self._models_cache is None or refresh:
            try:
                self._models_cache = self._config_manager.list_model_configs()
            except Exception as e:
                print(f"错误：加载模型配置失败：{e}")
                self._models_cache = []
        return self._models_cache

    def get_database_config(self, refresh: bool = False) -> Dict:
        """
        获取数据库配置

        Args:
            refresh: 是否刷新缓存

        Returns:
            数据库配置字典
        """
        if self._db_config_cache is None or refresh:
            try:
                self._db_config_cache = self._config_manager.get_database_config()
            except Exception as e:
                print(f"错误：加载数据库配置失败：{e}")
                self._db_config_cache = {}
        return self._db_config_cache

    def get_database_path(self) -> Path:
        """
        获取数据库路径 - 返回 Path 对象而非字符串

        GUI 不需要知道 db_paths 的解析逻辑，只需要一个可用的路径

        Returns:
            数据库文件路径
        """
        db_config = self.get_database_config()
        db_path_dict = db_config.get('db_paths', {})

        if db_path_dict:
            # 返回第一个数据库路径
            db_path_str = next(iter(db_path_dict.values()))
        else:
            db_path_str = db_config.get('db_path', 'data/poetry.db')

        return self._project_root / db_path_str

    def get_categories_paths(self) -> Dict[str, Optional[str]]:
        """
        获取情感分类文件路径

        Returns:
            {'xml_path': str, 'md_path': str}
        """
        try:
            categories_config = self._config_manager.get_categories_config()
            result = {}

            # 优先使用配置中的路径
            if categories_config.get('xml_path'):
                xml_path = self._project_root / categories_config['xml_path']
                result['xml_path'] = str(xml_path) if xml_path.exists() else None
            else:
                # 默认路径
                default_xml = self._project_root / "data" / "categories.xml"
                result['xml_path'] = str(default_xml) if default_xml.exists() else None

            if categories_config.get('md_path'):
                md_path = self._project_root / categories_config['md_path']
                result['md_path'] = str(md_path) if md_path.exists() else None
            else:
                # 默认路径
                default_md = self._project_root / "data" / "中国古典诗词情感分类体系.md"
                result['md_path'] = str(default_md) if default_md.exists() else None

            return result
        except Exception as e:
            print(f"获取情感分类路径失败：{e}")
            return {'xml_path': None, 'md_path': None}

    def get_data_paths(self) -> Dict[str, Path]:
        """
        获取数据目录路径

        Returns:
            {'source_dir': Path, 'output_dir': Path}
        """
        try:
            data_config = self._config_manager.get_data_config()
            return {
                'source_dir': self._project_root / data_config.get('source_dir', 'data'),
                'output_dir': self._project_root / data_config.get('output_dir', 'output')
            }
        except Exception as e:
            print(f"获取数据路径失败：{e}")
            return {
                'source_dir': self._project_root / "data",
                'output_dir': self._project_root / "output"
            }

    def get_model_display_name(self, model_name: str) -> str:
        """
        获取模型的显示名称（包含 provider 信息）

        Args:
            model_name: 模型配置名称

        Returns:
            格式化后的显示名称
        """
        try:
            models = self._config_manager.list_model_configs()
            if model_name in models:
                return model_name
        except:
            pass
        return model_name

    def validate_model(self, model_name: str) -> bool:
        """
        验证模型名称是否有效

        Args:
            model_name: 模型名称

        Returns:
            是否有效
        """
        if not model_name or "无" in model_name or "失败" in model_name:
            return False
        return model_name in self.list_models()

    def validate_database(self) -> bool:
        """
        验证数据库配置是否有效

        Returns:
            是否有效
        """
        try:
            db_path = self.get_database_path()
            return db_path.exists()
        except:
            return False
