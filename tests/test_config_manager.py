"""
配置管理器模块的单元测试
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

from src.config.manager import ConfigManager
from src.config.schema import GlobalConfig, ProjectConfig


class TestConfigManager(unittest.TestCase):
    """测试ConfigManager类"""

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

    def test_config_manager_initialization(self):
        """测试ConfigManager的初始化"""
        # 测试使用自定义路径初始化
        config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        # 验证配置对象已正确初始化
        self.assertIsInstance(config_manager.global_config, GlobalConfig)
        self.assertIsInstance(config_manager.project_config, ProjectConfig)
        
        # 验证配置文件路径
        self.assertEqual(config_manager.global_config_path, self.global_config_path)
        self.assertEqual(config_manager.project_config_path, self.project_config_path)

    def test_load_global_config(self):
        """测试加载全局配置"""
        config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        # 验证LLM配置
        llm_config = config_manager.get_llm_config()
        self.assertEqual(llm_config['max_workers'], 2)
        self.assertEqual(llm_config['max_retries'], 5)
        self.assertEqual(llm_config['save_full_response'], True)
        
        # 验证数据库配置
        db_config = config_manager.get_effective_database_config()
        self.assertIn('db_paths', db_config)
        self.assertEqual(db_config['db_paths']['TestDB'], 'data/test.db')
        
        # 验证数据路径配置
        data_config = config_manager.get_effective_data_config()
        self.assertEqual(data_config['source_dir'], 'data/source_json')
        self.assertEqual(data_config['output_dir'], 'data/output')
        
        # 验证日志配置
        log_config = config_manager.get_effective_logging_config()
        self.assertEqual(log_config['console_log_level'], 'DEBUG')
        self.assertEqual(log_config['max_file_size'], 50)
        
        # 验证可视化配置
        viz_config = config_manager.get_effective_visualizer_config()
        self.assertEqual(viz_config['enable_custom_download'], True)
        
        # 验证模型配置
        model_configs = config_manager.get_effective_model_configs()
        self.assertEqual(len(model_configs), 1)
        self.assertEqual(model_configs[0]['model_name'], 'test-model')

    def test_load_project_config(self):
        """测试加载项目配置"""
        config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        # 验证项目配置已加载
        self.assertIsNotNone(config_manager.project_config)
        
        # 验证项目数据库配置
        db_config = config_manager.get_effective_database_config()
        self.assertIn('separate_db_paths', db_config)
        self.assertEqual(db_config['separate_db_paths']['raw_data'], 'data/TestDB/raw_data.db')
        
        # 验证项目模型配置
        model_configs = config_manager.get_effective_model_configs()
        self.assertEqual(len(model_configs), 1)
        self.assertEqual(model_configs[0]['model_name'], 'test-model')

    def test_get_effective_configs(self):
        """测试获取生效配置"""
        config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        # 测试获取生效的数据库配置
        db_config = config_manager.get_effective_database_config()
        self.assertIn('db_paths', db_config)
        self.assertIn('separate_db_paths', db_config)
        
        # 测试获取生效的数据配置
        data_config = config_manager.get_effective_data_config()
        self.assertEqual(data_config['source_dir'], 'data/source_json')
        self.assertEqual(data_config['output_dir'], 'data/output')
        
        # 测试获取生效的提示词配置
        prompt_config = config_manager.get_effective_prompt_config()
        self.assertEqual(prompt_config, {})
        
        # 测试获取生效的日志配置
        log_config = config_manager.get_effective_logging_config()
        self.assertEqual(log_config['console_log_level'], 'DEBUG')
        
        # 测试获取生效的可视化配置
        viz_config = config_manager.get_effective_visualizer_config()
        self.assertEqual(viz_config['enable_custom_download'], True)
        
        # 测试获取生效的模型配置
        model_configs = config_manager.get_effective_model_configs()
        self.assertEqual(len(model_configs), 1)
        
        # 测试获取生效的规则集名称
        self.assertEqual(config_manager.get_effective_validation_ruleset_name(), 'default_emotion_annotation')
        self.assertEqual(config_manager.get_effective_preprocessing_ruleset_name(), 'social_emotion')
        self.assertEqual(config_manager.get_effective_cleaning_ruleset_name(), 'default')

    def test_save_global_config(self):
        """测试保存全局配置"""
        config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        # 修改全局配置
        config_manager.global_config.llm.max_workers = 5
        config_manager.global_config.logging.console_log_level = 'ERROR'
        
        # 保存配置
        config_manager.save_global_config()
        
        # 重新加载配置并验证
        new_config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        llm_config = new_config_manager.get_llm_config()
        self.assertEqual(llm_config['max_workers'], 5)
        
        log_config = new_config_manager.get_effective_logging_config()
        self.assertEqual(log_config['console_log_level'], 'ERROR')

    def test_save_project_config(self):
        """测试保存项目配置"""
        config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        # 修改项目配置
        config_manager.project_config.model.model_names = ['TestModel', 'AnotherModel']
        
        # 保存配置
        config_manager.save_project_config()
        
        # 重新加载配置并验证
        new_config_manager = ConfigManager(
            global_config_path=self.global_config_path,
            project_config_path=self.project_config_path,
            config_metadata_path=self.config_metadata_path
        )
        
        model_configs = new_config_manager.get_effective_model_configs()
        self.assertEqual(len(model_configs), 2)


if __name__ == '__main__':
    unittest.main()