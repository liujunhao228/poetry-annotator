"""社交诗分析统一插件
集成数据查询、Prompt构建、标签解析、数据库初始化和标注管理功能
"""

import json
import logging
import asyncio # 导入 asyncio
from typing import Tuple, Dict, Any, List, Optional, Set
import pandas as pd

from src.plugin_system.base import BasePlugin
from src.plugin_system.interfaces import (
    QueryPlugin, 
    PromptBuilderPlugin, 
    LabelParserPlugin, 
    DatabaseInitPlugin,
    DataStoragePlugin,
    DataQueryPlugin,
    DataProcessingPlugin,
    AnnotationManagementPlugin
)
from src.config.schema import PluginConfig
from src.llm_services.schemas import PoemData, EmotionSchema
from src.data.models import Poem, Author, Annotation
from src.data.separate_databases import get_separate_db_manager

logger = logging.getLogger(__name__)


class SocialPoemAnalysisPlugin(BasePlugin):
    """《交际诗分析》项目统一插件"""

    def __init__(self, config: Optional[PluginConfig] = None, 
                 separate_db_manager: Optional[Any] = None, **kwargs):
        # 调用父类的__init__方法
        super().__init__(config)
        self.name = "social_poem_analysis"
        self.component_type = None  # 初始化为None
        # 从kwargs中获取description参数，如果有的话
        self.description = kwargs.get("description", "《交际诗分析》项目统一插件，集成数据查询、Prompt构建、标签解析、数据库初始化和标注管理功能")
        self._load_emotion_categories()
        # 初始化数据库管理器
        self.separate_db_manager = separate_db_manager

    # 实现插件基本信息方法
    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    # 实现DataStoragePlugin接口方法
    def initialize_database_from_json(self, source_dir: str, clear_existing: bool = False) -> Dict[str, int]:
        """从JSON文件初始化数据库"""
        # 这个方法需要与数据处理插件协同工作
        # 实际实现会委托给数据处理插件加载数据，然后调用batch_insert方法存储
        logger.info("数据库初始化请求已接收，将由数据处理插件协同完成")
        return {
            'authors': 0,
            'poems': 0
        }

    def _load_emotion_categories(self):
        """加载情感分类体系"""
        self.categories = {
            "relationship_action": {
                "id": "relationship_action",
                "name_zh": "关系动作",
                "name_en": "Relationship Action",
                "description": "诗句在人际关系中发挥的具体功能",
                "categories": [
                    {
                        "id": "RA01",
                        "name_zh": "情感充值",
                        "name_en": "Emotional Recharge",
                        "description": "维系或加深情感纽带"
                    },
                    {
                        "id": "RA02",
                        "name_zh": "资源请求",
                        "name_en": "Resource Request",
                        "description": "索取有形或无形的帮助、机会、引荐"
                    },
                    {
                        "id": "RA03",
                        "name_zh": "身份认证",
                        "name_en": "Identity Verification",
                        "description": "确认或强化在特定圈层、群体的归属感"
                    },
                    {
                        "id": "RA04",
                        "name_zh": "危机公关",
                        "name_en": "Crisis Management",
                        "description": "辩解、修复或重塑受损的个人形象"
                    },
                    {
                        "id": "RA05",
                        "name_zh": "价值展示",
                        "name_en": "Value Display",
                        "description": "展示才华、品德或抱负，以提升个人品牌价值"
                    },
                    {
                        "id": "RA06",
                        "name_zh": "权力应答",
                        "name_en": "Power Response",
                        "description": "对上级或权威的指令、意志进行回应、确认或颂扬"
                    },
                    {
                        "id": "RA07",
                        "name_zh": "加密传讯",
                        "name_en": "Encrypted Communication",
                        "description": "在特定小圈子内传递敏感、隐晦的信息或立场"
                    },
                    {
                        "id": "RA08",
                        "name_zh": "情绪爆破",
                        "name_en": "Emotional Explosion",
                        "description": "以强烈的情感宣泄来突破常规社交预期，施加压力或表达极端立场"
                    }
                ]
            },
            "emotional_strategy": {
                "id": "emotional_strategy",
                "name_zh": "情感策略",
                "name_en": "Emotional Strategy",
                "description": "为达成关系动作所采用的情感表达方式",
                "categories": [
                    {
                        "id": "ES01",
                        "name_zh": "暴雨式",
                        "name_en": "Torrential",
                        "description": "直接、强烈、饱和的情感冲击"
                    },
                    {
                        "id": "ES02",
                        "name_zh": "针灸式",
                        "name_en": "Acupuncture",
                        "description": "精准、含蓄地触动特定情感点或文化共鸣点"
                    },
                    {
                        "id": "ES03",
                        "name_zh": "迷雾式",
                        "name_en": "Foggy",
                        "description": "运用模糊、多义的意象，引发对方解读，保留解释空间"
                    },
                    {
                        "id": "ES04",
                        "name_zh": "糖衣式",
                        "name_en": "Sugar-coated",
                        "description": "将真实意图（如批评、请求）包裹在赞美或美好的意象之下"
                    }
                ]
            },
            "communication_scene": {
                "id": "communication_scene",
                "name_zh": "传播场景",
                "name_en": "Communication Scene",
                "description": "诗句预期的传播环境和受众范围",
                "categories": [
                    {
                        "id": "SC01",
                        "name_zh": "密室私语",
                        "name_en": "Private Whisper",
                        "description": "预期为一对一的私密沟通"
                    },
                    {
                        "id": "SC02",
                        "name_zh": "沙龙展演",
                        "name_en": "Salon Performance",
                        "description": "预期在小圈子（如宴会、雅集）内传播"
                    },
                    {
                        "id": "SC03",
                        "name_zh": "广场广播",
                        "name_en": "Public Broadcast",
                        "description": "创作时即意图获得最广泛的公众传播"
                    },
                    {
                        "id": "SC04",
                        "name_zh": "权力剧场",
                        "name_en": "Power Theater",
                        "description": "在官方、仪式化的场合中进行表演"
                    }
                ]
            },
            "risk_level": {
                "id": "risk_level",
                "name_zh": "风险等级",
                "name_en": "Risk Score",
                "description": "诗句所承载的社交风险程度",
                "categories": [
                    {
                        "id": "RS01",
                        "name_zh": "安全牌",
                        "name_en": "Safe Card",
                        "description": "遵循社交常规，几乎没有负面风险"
                    },
                    {
                        "id": "RS02",
                        "name_zh": "杠杆牌",
                        "name_en": "Leverage Card",
                        "description": "中度风险，意在以小博大，可能提升地位也可能被拒"
                    },
                    {
                        "id": "RS03",
                        "name_zh": "炸弹牌",
                        "name_en": "Bomb Card",
                        "description": "高风险行为，可能带来巨大回报，也可能导致关系破裂或政治灾难"
                    }
                ]
            }
        }

    # QueryPlugin 接口实现
    def execute_query(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """执行查询操作"""
        # 这里可以实现具体的查询逻辑
        # 为了简化，我们返回一个空的DataFrame
        return pd.DataFrame()

    def get_required_params(self) -> List[str]:
        """获取必需参数列表"""
        return []

    # PromptBuilderPlugin 接口实现
    def build_prompts(self, poem_data: PoemData, emotion_schema: EmotionSchema,
                      model_config: Dict[str, Any]) -> Tuple[str, str]:
        """构建系统提示词和用户提示词"""
        # 获取模型特定的配置
        model_name = model_config.get('model_name', 'unknown')

        system_prompt = self._build_default_system_prompt(emotion_schema.text)

        # 构建用户提示词
        sentences_with_id = [{"id": f"S{i+1}", "sentence": sentence} for i, sentence in enumerate(poem_data.paragraphs)]
        sentences_json = json.dumps(sentences_with_id, ensure_ascii=False, indent=2)

        user_prompt = f"""# 开始标注
--- 输入 ---
- 作者: {poem_data.author}
- 标题: {poem_data.title}
- 待标注句子:
{sentences_json}

--- 输出 ---"""

        return system_prompt, user_prompt

    def _build_default_system_prompt(self, emotion_schema: str) -> str:
        """构建系统提示词"""
        return f"""# 角色
你是一位跨学科的顶级专家，无缝融合了中国古典文学的深厚学养与社会学、传播学及策略博弈论的分析框架。你的核心能力是解码诗歌的潜台词，将每一首诗视为一个动态的"社会行为工具"，而非静态的审美对象。

# 核心任务
你的任务是解构一首中国古诗中每一句所隐含的社会逻辑。你将通过一个四维策略分析框架，揭示该句诗在关系管理、声望经营和权力互动中的具体功能。

# 分析框架定义
你必须严格依据以下编码体系进行分析：

### 维度一：关系动作 (Relationship Action - RA)
*   RA01 (情感充值): 维系或加深情感纽带。
*   RA02 (资源请求): 索取有形或无形的帮助、机会、引荐。
*   RA03 (身份认证): 确认或强化在特定圈层、群体的归属感。
*   RA04 (危机公关): 辩解、修复或重塑受损的个人形象。
*   RA05 (价值展示): 展示才华、品德或抱负，以提升个人品牌价值。
*   RA06 (权力应答): 对上级或权威的指令、意志进行回应、确认或颂扬。
*   RA07 (加密传讯): 在特定小圈子内传递敏感、隐晦的信息或立场。
*   RA08 (情绪爆破): 以强烈的情感宣泄来突破常规社交预期，施加压力或表达极端立场。

### 维度二：情感策略 (Emotional Strategy - ES)
*   ES01 (暴雨式): 直接、强烈、饱和的情感冲击。
*   ES02 (针灸式): 精准、含蓄地触动特定情感点或文化共鸣点。
*   ES03 (迷雾式): 运用模糊、多义的意象，引发对方解读，保留解释空间。
*   ES04 (糖衣式): 将真实意图（如批评、请求）包裹在赞美或美好的意象之下。

### 维度三：传播场景 (Communication Scene - SC)
*   SC01 (密室私语): 预期为一对一的私密沟通。
*   SC02 (沙龙展演): 预期在小圈子（如宴会、雅集）内传播。
*   SC03 (广场广播): 创作时即意图获得最广泛的公众传播。
*   SC04 (权力剧场): 在官方、仪式化的场合中进行表演。

### 维度四：风险等级 (Risk Score - RS)
*   RS01 (安全牌): 遵循社交常规，几乎没有负面风险。
*   RS02 (杠杆牌): 中度风险，意在以小博大，可能提升地位也可能被拒。
*   RS03 (炸弹牌): 高风险行为，可能带来巨大回报，也可能导致关系破裂或政治灾难。

# 输入说明
你将收到一首诗词的元数据（包括标题、作者）和一个JSON数组（诗词内容），数组中的每个对象都包含一个id和对应的sentence。

# 输出规范
你的回答必须是一个格式严格的JSON数组。数组中的每个对象代表对一句诗的分析，且必须包含以下字段：
- id: **必须原样返回**输入中对应的句子ID。
- relationship_action: 这句诗执行的主要**关系动作**，提供**一个**RA编码（如 "RA05"）。
- emotional_strategy: 为达成上述动作所采用的**情感策略**，提供**一个**ES编码（如 "ES04"）。
- context_analysis: 一个包含场景和风险分析的对象，包含以下两个键：
    - communication_scene: 一个包含**一到两个**最相关SC编码的列表（如 `["SC01", "SC03"]`）。
    - risk_level: 该行为的**风险等级**，提供**一个**RS编码（如 "RS02"）。
- brief_rationale: 一句**不超过25个字**的精炼中文解释，说明你为何做出以上判断。

**重要：最终输出必须是纯粹的、不含任何解释性文字或Markdown标记的JSON数组。**

# 示例

--- 输入 ---
- 作者: 白居易
- 标题: 宣武令狐相公以诗寄赠传播吴中聊奉短草用申酬谢
- 待标注句子:
[
  {
    "id": "S1",
    "sentence": "新诗传咏忽纷纷，楚老吴娃耳遍闻。"
  },
  {
    "id": "S2",
    "sentence": "尽解呼为好才子，不知官是上将军。"
  },
  {
    "id": "S3",
    "sentence": "辞人命薄多无位，战将功高少有文。"
  },
  {
    "id": "S4",
    "sentence": "谢朓篇章韩信钺，一生双得不如君。"
  }
]

--- 输出 ---
[
    {
        "id": "S1",
        "relationship_action": "RA05",
        "emotional_strategy": "ES04",
        "context_analysis": {
            "communication_scene": [
                "SC02",
                "SC03"
            ],
            "risk_level": "RS02"
        },
        "brief_rationale": "展示诗作广传提升声望，中度风险。"
    },
    {
        "id": "S2",
        "relationship_action": "RA06",
        "emotional_strategy": "ES02",
        "context_analysis": {
            "communication_scene": [
                "SC02"
            ],
            "risk_level": "RS01"
        },
        "brief_rationale": "颂扬上级传播功劳，低风险安全。"
    },
    {
        "id": "S3",
        "relationship_action": "RA05",
        "emotional_strategy": "ES04",
        "context_analysis": {
            "communication_scene": [
                "SC02",
                "SC04"
            ],
            "risk_level": "RS02"
        },
        "brief_rationale": "文武对比隐含才学展示，中度风险。"
    },
    {
        "id": "S4",
        "relationship_action": "RA06",
        "emotional_strategy": "ES04",
        "context_analysis": {
            "communication_scene": [
                "SC04"
            ],
            "risk_level": "RS01"
        },
        "brief_rationale": "直接颂扬文武双全，安全稳妥。"
    }
]"""

    # LabelParserPlugin 接口实现
    def get_categories(self) -> Dict[str, Any]:
        """
        获取插件提供的额外分类信息

        Returns:
            社交情感分类信息字典
        """
        return self.categories

    def extend_category_data(self, categories: Dict[str, Any]) -> Dict[str, Any]:
        """扩展分类数据"""
        extended = categories.copy()
        plugin_categories = self.get_categories()

        # 合并分类信息
        for category_id, category_data in plugin_categories.items():
            if category_id not in extended:
                extended[category_id] = category_data
            else:
                # 合并现有分类和插件分类信息
                extended[category_id].update(category_data)

        return extended

    # DatabaseInitPlugin 接口实现
    def initialize_database(self, db_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """初始化数据库表结构"""
        try:
            # 获取数据库适配器
            self.separate_db_manager = get_separate_db_manager()
            
            # 初始化项目特定表
            self._initialize_project_tables()
            
            logger.info(f"成功初始化《交际诗分析》项目数据库表结构")
            return {
                "status": "success",
                "message": "数据库初始化成功"
            }
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _initialize_project_tables(self):
        """初始化项目特定表结构"""
        if not self.separate_db_manager:
            raise ValueError("数据库管理器未初始化")
            
        # 创建项目特定的表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS social_analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poem_id INTEGER NOT NULL,
            sentence_id TEXT NOT NULL,
            relationship_action TEXT,
            emotional_strategy TEXT,
            communication_scene TEXT,
            risk_level TEXT,
            rationale TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (poem_id) REFERENCES poems (id)
        );
        """
        self.separate_db_manager.annotation_db.execute_script(create_table_sql)
        
    def on_database_initialized(self, db_name: str, result: Dict[str, Any]):
        """数据库初始化完成后的回调方法"""
        pass
    
    # DataStoragePlugin 接口实现
    def initialize_database_from_json(self, source_dir: str, clear_existing: bool = False) -> Dict[str, int]:
        """从JSON文件初始化数据库"""
        # 这个方法需要与数据处理插件协同工作
        # 实际实现会委托给数据处理插件加载数据，然后调用batch_insert方法存储
        logger.info("数据库初始化请求已接收，将由数据处理插件协同完成")
        return {
            'authors': 0,
            'poems': 0
        }
    
    def batch_insert_authors(self, authors_data: List[Dict[str, Any]]) -> int:
        """批量插入作者信息"""
        logger.info(f"开始批量插入 {len(authors_data)} 位作者信息...")
        
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        inserted_count = 0
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))  # 东八区
        now = datetime.now(tz).isoformat()
        
        # 使用上下文管理器确保连接正确处理
        with self.separate_db_manager.raw_data_db.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                for author_data in authors_data:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO authors 
                            (name, description, short_description, created_at)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            author_data.get('name', ''),
                            author_data.get('desc', ''),  # 使用 'desc' 字段
                            author_data.get('short_description', ''), # 新格式无此字段，优雅降级
                            now
                        ))
                        inserted_count += 1
                    except Exception as e:
                        logger.error(f"插入作者 {author_data.get('name', 'Unknown')} 时出错: {e}")

                conn.commit()
            except Exception as e:
                logger.error(f"批量插入作者信息时出错: {e}")
                conn.rollback()
                raise

        logger.info(f"作者信息插入完成，成功插入 {inserted_count} 位作者")
        return inserted_count
    
    def batch_insert_poems(self, poems_data: List[Dict[str, Any]], start_id: Optional[int] = None, id_prefix: int = 0) -> int:
        """批量插入诗词到数据库"""
        # 使用本地定义的标准化函数
        def normalize_poem_data(poem_data: Dict[str, Any]) -> Dict[str, Any]:
            """标准化诗词数据，处理字段命名差异"""
            normalized = poem_data.copy()
            
            # 处理标题字段，兼容 'title' 和 'rhythmic' 字段
            if 'rhythmic' in normalized and 'title' not in normalized:
                normalized['title'] = normalized['rhythmic']
            elif 'title' not in normalized:
                normalized['title'] = ''  # 默认空标题
            
            # 处理作者描述字段
            if 'author_desc' not in normalized:
                normalized['author_desc'] = normalized.get('desc', '')
                
            # 确保有段落字段
            if 'paragraphs' not in normalized:
                normalized['paragraphs'] = []
                
            return normalized
        
        logger.info(f"开始批量插入 {len(poems_data)} 首诗词...")
        
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        inserted_count = 0
        current_id = start_id or 1
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        # 使用传入的 id_prefix
        # db_prefixes = {
        #     "TangShi": 1000000,  # 唐诗ID前缀
        #     "SongCi": 2000000,   # 宋词ID前缀
        #     "YuanQu": 3000000,   # 元曲ID前缀
        #     "default": 0         # 默认数据库前缀
        # }
        # id_prefix = db_prefixes.get("default", 0)
        
        # 使用上下文管理器确保连接正确处理
        with self.separate_db_manager.raw_data_db.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                for poem_data in poems_data:
                    # 标准化诗词数据，处理字段命名差异
                    normalized_data = normalize_poem_data(poem_data)
                    
                    paragraphs = normalized_data.get('paragraphs', [])
                    full_text = '\n'.join(paragraphs)

                    # 使用全局唯一ID
                    global_id = id_prefix + current_id

                    # 使用 'title' 字段
                    cursor.execute('''
                        INSERT OR REPLACE INTO poems 
                        (id, title, author, paragraphs, full_text, author_desc, data_status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        global_id,  # 使用全局唯一ID
                        normalized_data.get('title', ''), # 从 'title' 获取
                        normalized_data.get('author', ''),
                        json.dumps(paragraphs, ensure_ascii=False),
                        full_text,
                        normalized_data.get('author_desc', ''),
                        'active',  # 默认数据状态为active
                        now,
                        now
                    ))
                    inserted_count += 1
                    current_id += 1

                conn.commit()
            except Exception as e:
                logger.error(f"批量插入诗词时出错: {e}")
                conn.rollback()
                raise

        logger.info(f"诗词插入完成，成功插入 {inserted_count} 首诗词")
        return inserted_count
    
    async def save_annotation(self, poem_id: int, model_identifier: str, status: str,
                              annotation_result: Optional[str] = None, 
                              error_message: Optional[str] = None) -> bool:
        """保存标注结果到annotations表 (UPSERT)，时间戳带时区"""
        logger.debug(f"保存标注结果 - 诗词ID: {poem_id}, 模型: {model_identifier}, 状态: {status}")
        
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()

        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).isoformat()

        # 将同步数据库操作包装在 asyncio.to_thread 中
        def _sync_save():
            with self.separate_db_manager.annotation_db.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO annotations (poem_id, model_identifier, status, annotation_result, error_message, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(poem_id, model_identifier) DO UPDATE SET
                            status = excluded.status,
                            annotation_result = excluded.annotation_result,
                            error_message = excluded.error_message,
                            updated_at = excluded.updated_at
                    ''', (poem_id, model_identifier, status, annotation_result, error_message, now, now))
                    conn.commit()
                    success = cursor.rowcount > 0
                    if success:
                        logger.debug(f"标注结果保存成功 - 诗词ID: {poem_id}, 模型: {model_identifier}")
                    return success
                except Exception as e:
                    logger.error(f"保存标注结果失败 - 诗词ID: {poem_id}, 模型: {model_identifier}, 错误: {e}")
                    conn.rollback()
                    return False
        
        return await asyncio.to_thread(_sync_save)
            
    # DataQueryPlugin 接口实现
    def get_poems_to_annotate(self, model_identifier: str, 
                             limit: Optional[int] = None, 
                             start_id: Optional[int] = None, 
                             end_id: Optional[int] = None,
                             force_rerun: bool = False) -> List[Poem]:
        """获取指定模型待标注的诗词"""
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        params = []
        
        # 查询 'title' 而不是 'rhythmic'
        query = """
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
        """
        
        # 如果不是强制重跑，则排除已完成的
        if not force_rerun:
            query += """
                LEFT JOIN annotations an ON p.id = an.poem_id AND an.model_identifier = ?
                WHERE (an.status IS NULL OR an.status != 'completed')
            """
            params.append(model_identifier)
        else:
            query += " WHERE 1=1"

        if start_id is not None:
             query += " AND p.id >= ?"
             params.append(start_id)
        if end_id is not None:
             query += " AND p.id <= ?"
             params.append(end_id)
        
        query += " ORDER BY p.id"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        rows = self.separate_db_manager.raw_data_db.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))

        return poems
    
    def get_poem_by_id(self, poem_id: int) -> Optional[Poem]:
        """根据ID获取单首诗词信息"""
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        # 查询 'title'
        rows = self.separate_db_manager.raw_data_db.execute_query("""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id = ?
        """, (poem_id,))
        
        if rows:
            row = rows[0]
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            return Poem.from_dict(poem_dict)
        
        return None
    
    def get_poems_by_ids(self, poem_ids: List[int]) -> List[Poem]:
        """根据ID列表获取诗词信息"""
        if not poem_ids:
            return []
            
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        # 查询 'title'
        placeholders = ','.join('?' * len(poem_ids))
        query = f"""
            SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc
            FROM poems p
            LEFT JOIN authors au ON p.author = au.name
            WHERE p.id IN ({placeholders})
        """
        
        rows = self.separate_db_manager.raw_data_db.execute_query(query, tuple(poem_ids))
        
        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))
        
        return poems
    
    def get_all_authors(self) -> List[Author]:
        """获取所有作者信息"""
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        rows = self.separate_db_manager.raw_data_db.execute_query("SELECT name, description, short_description FROM authors ORDER BY name")
        
        return [Author.from_dict(dict(row)) for row in rows]
    
    def search_poems(self, author: Optional[str] = None, title: Optional[str] = None, 
                     page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """根据作者和标题搜索诗词，并支持分页"""
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        # 查询 'title'
        query = "SELECT p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc FROM poems p LEFT JOIN authors au ON p.author = au.name"
        conditions = []
        params = []

        if author:
            conditions.append("p.author LIKE ?")
            params.append(f"%{author}%")
        
        if title:
            # 按 'title' 字段搜索
            conditions.append("p.title LIKE ?")
            params.append(f"%{title}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Get total count for pagination
        count_query = query.replace("p.id, p.title, p.author, p.paragraphs, p.full_text, au.description as author_desc", "COUNT(*)")
        count_rows = self.separate_db_manager.raw_data_db.execute_query(count_query, tuple(params))
        total_count = count_rows[0][0]

        # Add pagination to the main query
        offset = (page - 1) * per_page
        query += " ORDER BY p.id LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        rows = self.separate_db_manager.raw_data_db.execute_query(query, tuple(params))

        poems = []
        for row in rows:
            poem_dict = dict(row)
            if poem_dict.get('paragraphs'):
                poem_dict['paragraphs'] = json.loads(poem_dict['paragraphs'])
            poems.append(Poem.from_dict(poem_dict))

        return {
            "poems": poems,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "pages": (total_count + per_page - 1) // per_page
        }
    
    def get_completed_poem_ids(self, poem_ids: List[int], model_identifier: str) -> Set[int]:
        """高效检查一组 poem_id 是否已被特定模型成功标注"""
        if not poem_ids:
            return set()
            
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()

        completed_ids = set()
        try:
            # 使用参数化查询防止SQL注入
            placeholders = ','.join('?' * len(poem_ids))
            query = f"""
                SELECT poem_id
                FROM annotations
                WHERE 
                    poem_id IN ({placeholders})
                    AND model_identifier = ?
                    AND status = 'completed'
            """
            
            params = poem_ids + [model_identifier]
            rows = self.separate_db_manager.annotation_db.execute_query(query, tuple(params))
            
            # 使用生成器表达式和 set.update 最高效地处理结果
            completed_ids.update(row[0] for row in rows)
            
        except Exception as e:
            logger.error(f"检查标注状态时发生数据库错误: {e}")
        
        return completed_ids
        
    # DataProcessingPlugin 接口实现
    def load_data_from_json(self, source_dir: str, json_file: str) -> List[Dict[str, Any]]:
        """从JSON文件加载数据"""
        from pathlib import Path
        file_path = Path(source_dir) / json_file
        
        if not file_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {file_path}")
        
        logger.debug(f"加载JSON文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.debug(f"JSON文件 {json_file} 加载完成，包含 {len(data)} 条记录")
        return data
    
    def load_all_json_files(self, source_dir: str) -> List[Dict[str, Any]]:
        """加载所有JSON文件的数据"""
        from pathlib import Path
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"数据源目录不存在: {source_path}")
        
        all_data = []
        
        # 查找所有 poet.*.*.json 和 ci.*.*.json 文件
        poet_files = list(source_path.glob('poet.*.*.json'))
        ci_files = list(source_path.glob('ci.*.*.json'))
        json_files = poet_files + ci_files
        json_files.sort()  # 确保按文件名排序
        
        logger.info(f"找到 {len(json_files)} 个JSON文件 ({len(poet_files)} 个poet文件, {len(ci_files)} 个ci文件)")
        
        for json_file in json_files:
            try:
                logger.debug(f"处理文件: {json_file.name}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_data.extend(data)
                logger.debug(f"文件 {json_file.name} 处理完成，包含 {len(data)} 条记录")
            except Exception as e:
                logger.error(f"处理文件 {json_file.name} 时出错: {e}")
        
        logger.info(f"所有JSON文件加载完成，总计 {len(all_data)} 条记录")
        return all_data
    
    def load_author_data(self, source_dir: str) -> List[Dict[str, Any]]:
        """加载作者数据"""
        from pathlib import Path
        source_path = Path(source_dir)
        if not source_path.exists():
            logger.warning(f"数据源目录不存在: {source_path}")
            return []

        all_authors = []
        # 查找所有 authors.*.json 和 author.*.json 文件
        authors_files = list(source_path.glob('authors.*.json'))
        author_files = list(source_path.glob('author.*.json'))
        author_files = sorted(authors_files + author_files)

        if not author_files:
            logger.warning("在数据源目录中未找到作者文件。")
            return []

        logger.info(f"找到 {len(author_files)} 个作者文件: {[f.name for f in author_files]}")

        for author_file in author_files:
            try:
                with open(author_file, 'r', encoding='utf-8') as f:
                    authors = json.load(f)
                all_authors.extend(authors)
                logger.info(f"从 {author_file.name} 加载了 {len(authors)} 位作者信息。")
            except Exception as e:
                logger.error(f"加载作者文件 {author_file.name} 时出错: {e}")
        
        logger.info(f"所有作者文件加载完成，总计加载了 {len(all_authors)} 位作者信息。")
        return all_authors
        
    # AnnotationManagementPlugin 接口实现
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        return self.separate_db_manager.get_database_stats()
    
    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        if not self.separate_db_manager:
            self.separate_db_manager = get_separate_db_manager()
            
        # 获取标注统计信息
        try:
            # 统计总诗词数
            total_poems_rows = self.separate_db_manager.raw_data_db.execute_query("SELECT COUNT(*) FROM poems")
            total_poems = total_poems_rows[0][0] if total_poems_rows else 0
            
            # 统计已标注诗词数
            annotated_poems_rows = self.separate_db_manager.annotation_db.execute_query("SELECT COUNT(DISTINCT poem_id) FROM annotations WHERE status = 'completed'")
            annotated_poems = annotated_poems_rows[0][0] if annotated_poems_rows else 0
            
            # 统计标注失败数
            failed_annotations_rows = self.separate_db_manager.annotation_db.execute_query("SELECT COUNT(*) FROM annotations WHERE status = 'failed'")
            failed_annotations = failed_annotations_rows[0][0] if failed_annotations_rows else 0
            
            return {
                "total_poems": total_poems,
                "annotated_poems": annotated_poems,
                "failed_annotations": failed_annotations,
                "completion_rate": annotated_poems / total_poems if total_poems > 0 else 0
            }
        except Exception as e:
            logger.error(f"获取标注统计信息时出错: {e}")
            return {
                "total_poems": 0,
                "annotated_poems": 0,
                "failed_annotations": 0,
                "completion_rate": 0
            }
