# Poetry Annotator Package
__version__ = "1.0.0"

import os
import sys

# 确保 src 目录在 sys.path 中，以便处理相对导入和绝对导入
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 导入核心模块
from .batch_logger import batch_logger_manager, get_batch_logger

# 导入核心模块
from .batch_logger import batch_logger_manager, get_batch_logger 