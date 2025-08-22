import os
import sys
from pathlib import Path

# 计算项目根目录 (E:\poetry-annotator) 和可视化模块根目录
# __file__ is E:\poetry-annotator\poetry-annotator-data-visualizer\data_visualizer\config.py
# Parent directories: data_visualizer -> poetry-annotator-data-visualizer -> poetry-annotator (project root)
visualizer_module_root = Path(__file__).parent # data_visualizer
visualizer_project_root = Path(__file__).parent.parent # poetry-annotator-data-visualizer
project_root = Path(__file__).parent.parent.parent # poetry-annotator (main project root)

# 确保主项目路径被添加，以便导入 src 下的模块
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
# 确保可视化模块根路径也被添加，以便导入其内部模块
# 这对于导入 data_visualizer 包内的其他模块（如 app/）可能很重要
if str(visualizer_project_root) not in sys.path:
    sys.path.insert(0, str(visualizer_project_root))

# --- 从这里开始，导入主项目的 config_manager 应该可以工作 ---
# 导入主项目的配置管理器
try:
    from src.config import config_manager  # 这应该可以工作了
    # 从主项目配置获取数据库路径
    db_config = config_manager.get_effective_database_config()
    
    # 解析主项目配置中的数据库路径，并确保使用绝对路径
    if 'db_paths' in db_config:
        # 使用主项目配置中的多数据库配置，转换为绝对路径
        DB_PATHS = {}
        for name, path in db_config['db_paths'].items():
            # 如果是相对路径，则相对于项目根目录解析
            if not os.path.isabs(path):
                DB_PATHS[name] = os.path.join(str(project_root), path)
            else:
                DB_PATHS[name] = path
    elif 'db_path' in db_config:
        # 兼容旧的单数据库配置
        path = db_config['db_path']
        if not os.path.isabs(path):
            abs_path = os.path.join(str(project_root), path)
        else:
            abs_path = path
        DB_PATHS = {"default": abs_path}
    else:
        # 如果主项目没有配置数据库路径，则使用默认值
        DB_PATHS = {
            "TangShi": os.path.join(str(project_root), 'data', 'TangShi.db'),
            "SongCi": os.path.join(str(project_root), 'data', 'SongCi.db'),
        }
        
    # 获取可视化相关配置
    visualizer_config = config_manager.get_effective_visualizer_config()
    ENABLE_CUSTOM_DOWNLOAD = visualizer_config.get('enable_custom_download', False)
except Exception as e:
    print(f"无法从主项目配置管理器获取数据库配置: {e}")
    # Fallback to default configuration
    DB_PATHS = {
        "TangShi": os.path.join(str(project_root), 'data', 'TangShi.db'),
        "SongCi": os.path.join(str(project_root), 'data', 'SongCi.db'),
    }
    # 默认不启用自定义下载功能
    ENABLE_CUSTOM_DOWNLOAD = False

# 缓存配置
# 数据库查询结果最大缓存条数
CACHE_MAX_SIZE_DB_QUERIES = 50
# 数据处理结果最大缓存条数
CACHE_MAX_SIZE_DATA_PROCESSING = 30

# Streamlit 应用设置
APP_TITLE = "诗词与标注数据可视化分析平台"
