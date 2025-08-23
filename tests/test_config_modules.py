"""
配置管理器各模块的单元测试
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.metadata import load_config_metadata
from src.config.global_loader import GlobalConfigLoader
from src.config.project_loader import ProjectConfigLoader
from src.config.project_manager import ProjectConfigManager
from src.config.rules_loader import RulesLoader
from src.config.model_manager import ModelManager
from src.config.validator import ConfigValidator
from src.config.schema import GlobalConfig, ProjectConfig


class TestConfigModules(unittest.TestCase):
    """测试配置管理器的各个模块"""

    def setUp(self):
        """在每个测试方法运行前执行"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.global_config_path = os.path.join(self.config_dir, 'global', 'config.ini')
        self.project_config_path = os.path.join(self.config_dir, 'project', 'test_project.ini')
        self.active_project_path = os.path.join(self.config_dir, 'active_project.json')
        self.config_metadata_path = os.path.join(self.config_dir, 'config_metadata.json')
        
        # 创建目录结构
        os.makedirs(os.path.join(self.config_dir, 'global'), exist_ok=True)
        os.makedirs(os.path.join(self.config_dir, 'project'), exist_ok=True)
        
        # 创建全局配置文件
        global_config_content = """
[LLM]
max_workers = 2
max_model_pipelines = 2
max_retries = 5
retry_delay = 10
breaker_fail_max = 5
breaker_reset_timeout = 120
save_full_response = true

[Database]
db_paths = TestDB=data/test.db
separate_db_paths = raw_data=data/{main_db_name}/raw_data.db,annotation=data/{main_db_name}/annotation.db

[Data]
source_dir = data/source_json
output_dir = data/output

[Categories]
md_path = config/label/中国古典诗词主题分类体系.md
xml_path = config/label/emotion_categories.xml

[Prompt]

[Logging]
console_log_level = DEBUG
file_log_level = DEBUG
enable_file_log = True
log_file = 
enable_console_log = True
max_file_size = 50
backup_count = 10
quiet_third_party = False

[Visualizer]
enable_custom_download = true

[Model.TestModel]
provider = test
model_name = test-model
api_key = test-key
base_url = http://test.com
request_delay = 2.0
temperature = 0.8
max_tokens = 2000
timeout = 60
"""
        with open(self.global_config_path, 'w', encoding='utf-8') as f:
            f.write(global_config_content)
        
        # 创建项目配置文件
        project_config_content = """
[Database]
config_name = TestDB
separate_db_paths = raw_data=data/TestDB/raw_data.db,annotation=data/TestDB/annotation.db

[Data]
config_name = default
source_dir = data/source_json
output_dir = data/output

[Prompt]
config_name = default

[Model]
model_names = TestModel

[Validation]
ruleset_name = default_emotion_annotation

[Preprocessing]
ruleset_name = social_emotion

[Cleaning]
ruleset_name = default
"""
        with open(self.project_config_path, 'w', encoding='utf-8') as f:
            f.write(project_config_content)
        
        # 创建active_project.json
        active_project_content = """
{
  "active_project": "test_project.ini",
  "available_projects": [
    "test_project.ini"
  ]
}
"""
        with open(self.active_project_path, 'w', encoding='utf-8') as f:
            f.write(active_project_content)
        
        # 创建config_metadata.json
        config_metadata_content = """
{
  "global_config_file": "config/global/config.ini",
  "active_project_config_file": "config/active_project.json",
  "validation_rules": {
    "global_file": "config/global/global_validation_rules.yaml",
    "project_files": [
      "config/project/project_validation_rules.yaml"
    ]
  },
  "preprocessing_rules": {
    "global_file": "config/global/global_preprocessing_rules.yaml",
    "project_files": [
      "config/project/project_preprocessing_rules.yaml"
    ]
  },
  "cleaning_rules": {
    "global_file": "config/global/global_cleaning_rules.yaml",
    "project_files": [
      "config/project/project_cleaning_rules.yaml"
    ]
  }
}
"""
        with open(self.config_metadata_path, 'w', encoding='utf-8') as f:
            f.write(config_metadata_content)

    def tearDown(self):
        """在每个测试方法运行后执行"""
        # 清理临时目录
        shutil.rmtree(self.test_dir)

    def test_metadata_loader(self):
        """测试元数据加载器"""
        metadata = load_config_metadata(self.config_metadata_path)
        self.assertIn("global_config_file", metadata)
        self.assertIn("active_project_config_file", metadata)
        self.assertEqual(metadata["global_config_file"], "config/global/config.ini")

    def test_global_config_loader(self):
        """测试全局配置加载器"""
        loader = GlobalConfigLoader(self.global_config_path)
        config = loader.load()
        
        self.assertIsInstance(config, GlobalConfig)
        self.assertEqual(config.llm.max_workers, 2)
        self.assertEqual(config.logging.console_log_level, "DEBUG")
        
        # 测试保存功能
        config.llm.max_workers = 3
        loader.save(config)
        
        # 重新加载验证
        new_config = loader.load()
        self.assertEqual(new_config.llm.max_workers, 3)

    def test_project_config_loader(self):
        """测试项目配置加载器"""
        loader = ProjectConfigLoader(self.project_config_path)
        config = loader.load()
        
        self.assertIsInstance(config, ProjectConfig)
        self.assertEqual(config.model.model_names, ["TestModel"])
        
        # 测试保存功能
        config.model.model_names = ["TestModel", "AnotherModel"]
        loader.save(config)
        
        # 重新加载验证
        new_config = loader.load()
        self.assertEqual(len(new_config.model.model_names), 2)

    def test_project_config_manager(self):
        """测试项目配置管理器"""
        manager = ProjectConfigManager(config_file=self.active_project_path)
        
        # 测试获取激活的项目
        active_project = manager.get_active_project()
        self.assertEqual(active_project, "test_project.ini")
        
        # 测试获取可用项目
        available_projects = manager.get_available_projects()
        self.assertIn("test_project.ini", available_projects)
        
        # 测试添加项目
        manager.add_project("new_project.ini")
        available_projects = manager.get_available_projects()
        self.assertIn("new_project.ini", available_projects)
        
        # 测试设置激活项目
        manager.set_active_project("new_project.ini")
        active_project = manager.get_active_project()
        self.assertEqual(active_project, "new_project.ini")

    def test_rules_loader(self):
        """测试规则加载器"""
        metadata = load_config_metadata(self.config_metadata_path)
        loader = RulesLoader(metadata)
        
        # 测试获取验证规则文件
        validation_files = loader._get_validation_rules_files()
        self.assertIn("config/global/global_validation_rules.yaml", validation_files)
        
        # 测试获取预处理规则文件
        preprocessing_files = loader._get_preprocessing_rules_files()
        self.assertIn("config/global/global_preprocessing_rules.yaml", preprocessing_files)
        
        # 测试获取清洗规则文件
        cleaning_files = loader._get_cleaning_rules_files()
        self.assertIn("config/global/global_cleaning_rules.yaml", cleaning_files)

    def test_model_manager(self):
        """测试模型管理器"""
        manager = ModelManager(self.global_config_path)
        
        # 测试获取模型配置
        model_config = manager.get_model_config("TestModel")
        self.assertEqual(model_config["model_name"], "test-model")
        self.assertEqual(model_config["provider"], "test")
        
        # 测试获取所有模型配置
        all_models = manager._get_all_global_model_configs()
        self.assertEqual(len(all_models), 1)
        self.assertEqual(all_models[0]["model_name"], "test-model")
        
        # 测试获取生效的模型配置
        effective_models = manager.get_effective_model_configs(["TestModel"])
        self.assertEqual(len(effective_models), 1)
        self.assertEqual(effective_models[0]["model_name"], "test-model")

    def test_config_validator(self):
        """测试配置验证器"""
        validator = ConfigValidator(self.global_config_path)
        
        # 测试配置验证
        is_valid = validator.validate_config(self.project_config_path)
        self.assertTrue(is_valid)


if __name__ == '__main__':
    unittest.main()