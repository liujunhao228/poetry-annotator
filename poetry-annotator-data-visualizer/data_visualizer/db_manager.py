import sqlite3
import pandas as pd
from functools import lru_cache
from data_visualizer.config import DB_PATHS, CACHE_MAX_SIZE_DB_QUERIES
from data_visualizer.utils import logger, db_connect
from typing import Any

# 尝试导入 tqdm 用于进度显示
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

class DBManager:
    def __init__(self, db_path=DB_PATHS['SongCi']):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表和索引，兼容唐诗和宋词结构。"""
        logger.info(f"检查/初始化数据库架构于 {self.db_path}...")
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # poems 表兼容 title (唐诗) 和 rhythmic (宋词)
            # 统一使用 title 字段名，宋词数据导入时将 rhythmic 映射到 title
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS poems (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    paragraphs TEXT,
                    full_text TEXT,
                    author_desc TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')

            # --- 其他表结构保持不变 ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS annotations (
                    id INTEGER PRIMARY KEY, poem_id INTEGER, model_identifier TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('completed', 'failed')),
                    annotation_result TEXT, error_message TEXT, created_at TEXT, updated_at TEXT,
                    FOREIGN KEY(poem_id) REFERENCES poems(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authors (
                    name TEXT PRIMARY KEY, description TEXT, short_description TEXT, created_at TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_categories (
                    id TEXT PRIMARY KEY, name_zh TEXT NOT NULL, name_en TEXT,
                    parent_id TEXT, level INTEGER NOT NULL,
                    FOREIGN KEY(parent_id) REFERENCES emotion_categories(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sentence_annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, annotation_id INTEGER NOT NULL, poem_id INTEGER NOT NULL,
                    sentence_uid TEXT NOT NULL, sentence_text TEXT,
                    FOREIGN KEY(annotation_id) REFERENCES annotations(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sentence_emotion_links (
                    sentence_annotation_id INTEGER NOT NULL, emotion_id TEXT NOT NULL, is_primary BOOLEAN NOT NULL,
                    PRIMARY KEY (sentence_annotation_id, emotion_id),
                    FOREIGN KEY(sentence_annotation_id) REFERENCES sentence_annotations(id) ON DELETE CASCADE,
                    FOREIGN KEY(emotion_id) REFERENCES emotion_categories(id)
                )
            ''')

            # --- 索引保持不变 ---
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_poem_author ON poems(author)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_poem_model ON annotations(poem_id, model_identifier)')
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uidx_poem_model ON annotations(poem_id, model_identifier)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_status ON annotations(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotation_created_at ON annotations(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_poem_created_at ON poems(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_emotion_parent_id ON emotion_categories(parent_id)')
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uidx_sentence_ref ON sentence_annotations(annotation_id, sentence_uid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_link_emotion_id ON sentence_emotion_links(emotion_id)')

            conn.commit()
            logger.info("数据库架构检查/初始化完成。")
        except sqlite3.Error as e:
            logger.error(f"数据库初始化错误: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @lru_cache(maxsize=CACHE_MAX_SIZE_DB_QUERIES)
    def _execute_fetch_data_cached(self, query: str, hashable_params: tuple[tuple[str, Any], ...] | None) -> pd.DataFrame:
        conn = None
        try:
            conn = db_connect(self.db_path)
            actual_params = dict(hashable_params) if hashable_params else None
            df = pd.read_sql_query(query, conn, params=actual_params)
            logger.debug(f"从数据库获取 {len(df)} 行数据 (查询: {query[:100]}..., 参数: {actual_params})")
            return df
        except sqlite3.Error as e:
            logger.error(f"数据库查询失败: {e} | 查询: {query}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

    def _fetch_data(self, query: str, params: dict = None) -> pd.DataFrame:
        hashable_params = tuple(sorted(params.items())) if params is not None else None
        return self._execute_fetch_data_cached(query, hashable_params)

    def get_all_poems(self) -> pd.DataFrame:
        """获取所有诗词数据。"""
        # 兼容 title (唐诗) 和 rhythmic (宋词) 字段
        # 注：数据库表结构中只有 title 字段，宋词的 rhythmic 在导入时已映射到 title 字段
        query = """
            SELECT id, 
                   title AS title, 
                   author, paragraphs, full_text, created_at 
            FROM poems
        """
        return self._fetch_data(query)

    def get_all_annotations(self) -> pd.DataFrame:
        """获取所有标注数据。"""
        return self._fetch_data("SELECT id, poem_id, model_identifier, status, annotation_result, error_message, created_at FROM annotations")

    def get_all_authors(self) -> pd.DataFrame:
        """获取所有作者数据。"""
        return self._fetch_data("SELECT name, description, short_description FROM authors")

    def get_annotations_with_poem_info(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取标注数据并联接诗词信息，支持按日期过滤。"""
        # 兼容 title (唐诗) 和 rhythmic (宋词) 字段
        # 注：数据库表结构中只有 title 字段，宋词的 rhythmic 在导入时已映射到 title 字段
        query = """
            SELECT
                a.id AS annotation_id, a.model_identifier, a.status, a.created_at AS annotation_created_at,
                p.id AS poem_id, 
                p.title AS title, 
                p.author, p.created_at AS poem_created_at
            FROM annotations a
            JOIN poems p ON a.poem_id = p.id
            WHERE 1=1
        """
        params = {}
        if start_date:
            query += " AND a.created_at >= :start_date"
            params['start_date'] = start_date
        if end_date:
            query += " AND a.created_at <= :end_date"
            params['end_date'] = end_date
        return self._fetch_data(query, params)

    def get_poem_count_by_author(self) -> pd.DataFrame:
        """从数据库直接聚合，获取每个作者的诗词数量。"""
        query = "SELECT author, COUNT(id) AS poem_count FROM poems GROUP BY author ORDER BY poem_count DESC"
        return self._fetch_data(query)

    def get_annotation_summary_by_model(self) -> pd.DataFrame:
        """从数据库直接聚合，获取每个模型的标注状态统计。"""
        query = "SELECT model_identifier, status, COUNT(id) AS count FROM annotations GROUP BY model_identifier, status ORDER BY model_identifier, status"
        return self._fetch_data(query)

    def get_all_emotion_categories(self) -> pd.DataFrame:
        """获取所有情感分类定义。"""
        query = "SELECT id, name_zh, name_en, parent_id, level FROM emotion_categories"
        return self._fetch_data(query)

    def get_emotion_distribution(self) -> pd.DataFrame:
        """统计每种情感（无论主次）的出现次数。"""
        query = """
            SELECT ec.id, ec.name_zh, ec.parent_id, ec.level, COUNT(sel.emotion_id) AS count
            FROM sentence_emotion_links sel
            JOIN emotion_categories ec ON sel.emotion_id = ec.id
            GROUP BY ec.id ORDER BY count DESC
        """
        return self._fetch_data(query)

    def get_frequent_emotion_combinations(self, limit: int = 50) -> pd.DataFrame:
        """查找最频繁的单句内情感共现组合。"""
        query = """
            WITH SentenceEmotions AS (
                SELECT sel.sentence_annotation_id, GROUP_CONCAT(sel.emotion_id, ';' ORDER BY sel.emotion_id) AS emotion_combo_ids
                FROM sentence_emotion_links sel
                GROUP BY sel.sentence_annotation_id
                HAVING COUNT(sel.emotion_id) > 1
            ), ComboCounts AS (
                SELECT emotion_combo_ids, COUNT(*) as combo_count
                FROM SentenceEmotions GROUP BY emotion_combo_ids
            ), SentenceExample AS (
                SELECT se.emotion_combo_ids, MIN(sa.sentence_text) as sentence_text
                FROM SentenceEmotions se
                JOIN sentence_annotations sa ON se.sentence_annotation_id = sa.id
                GROUP BY se.emotion_combo_ids
            )
            SELECT cc.emotion_combo_ids, cc.combo_count, ex.sentence_text
            FROM ComboCounts cc JOIN SentenceExample ex ON cc.emotion_combo_ids = ex.emotion_combo_ids
            ORDER BY cc.combo_count DESC LIMIT :limit
        """
        return self._fetch_data(query, params={'limit': limit})

    def get_frequent_poem_emotion_sets(self, limit: int = 50) -> pd.DataFrame:
        """查找最频繁的全诗情感集合。"""
        # 兼容 title (唐诗) 和 rhythmic (宋词) 字段
        query = """
            WITH LatestCompletedAnnotation AS (
                SELECT poem_id, MAX(id) as annotation_id FROM annotations WHERE status = 'completed' GROUP BY poem_id
            ), PoemDistinctEmotions AS (
                SELECT DISTINCT sa.poem_id, sel.emotion_id
                FROM sentence_emotion_links sel
                JOIN sentence_annotations sa ON sel.sentence_annotation_id = sa.id
                JOIN LatestCompletedAnnotation lca ON sa.annotation_id = lca.annotation_id
            ), PoemEmotionSets AS (
                SELECT poem_id, GROUP_CONCAT(emotion_id, ';' ORDER BY emotion_id) as emotion_set_ids
                FROM PoemDistinctEmotions GROUP BY poem_id HAVING COUNT(emotion_id) > 1
            ), SetCounts AS (
                SELECT emotion_set_ids, COUNT(*) as set_count
                FROM PoemEmotionSets GROUP BY emotion_set_ids
            ), PoemExample AS (
                SELECT pes.emotion_set_ids, 
                       MIN(p.title || ' - ' || p.author) as poem_example
                FROM PoemEmotionSets pes JOIN poems p ON pes.poem_id = p.id GROUP BY pes.emotion_set_ids
            )
            SELECT sc.emotion_set_ids, sc.set_count, pe.poem_example
            FROM SetCounts sc JOIN PoemExample pe ON sc.emotion_set_ids = pe.emotion_set_ids
            ORDER BY sc.set_count DESC
            LIMIT :limit
        """
        return self._fetch_data(query, params={'limit': limit})

    def get_emotion_transactions(self, level: str = 'sentence') -> list[list[str]]:
        """
        获取用于关联规则挖掘的事务列表。
        每个子列表代表一个事务（一组情感ID）。
        :param level: 分析的层级，可以是 'sentence' 或 'poem'。
        :return: 一个列表，其中每个元素是代表一个事务的情感ID列表。
                 例如: [['E1', 'E2'], ['E1', 'E3', 'E4'], ...]
        """
        if level == 'sentence':
            # 句子级别：获取每个句子关联的所有情感
            # 过滤掉只有一个情感的句子，因为它们对共现分析无贡献
            query = """
                SELECT
                    GROUP_CONCAT(emotion_id, ';')
                FROM sentence_emotion_links
                GROUP BY sentence_annotation_id
                HAVING COUNT(emotion_id) > 1;
            """
        elif level == 'poem':
            # 诗词级别：获取每首诗（基于最新标注）的所有唯一情感
            # 使用 WITH 子句确保逻辑清晰
            query = """
                WITH LatestCompletedAnnotation AS (
                    SELECT poem_id, MAX(id) as annotation_id
                    FROM annotations
                    WHERE status = 'completed'
                    GROUP BY poem_id
                ),
                PoemDistinctEmotions AS (
                    SELECT DISTINCT sa.poem_id, sel.emotion_id
                    FROM sentence_emotion_links sel
                    JOIN sentence_annotations sa ON sel.sentence_annotation_id = sa.id
                    JOIN LatestCompletedAnnotation lca ON sa.annotation_id = lca.annotation_id
                )
                SELECT GROUP_CONCAT(emotion_id, ';')
                FROM PoemDistinctEmotions
                GROUP BY poem_id
                HAVING COUNT(emotion_id) > 1;
            """
        else:
            logger.error(f"不支持的事务层级: {level}")
            return []

        # _fetch_data 返回的是 DataFrame，我们需要提取第一列并处理
        df = self._fetch_data(query)
        if df.empty:
            return []
        
        # 显示进度信息
        total_rows = len(df)
        if TQDM_AVAILABLE and total_rows > 1000:
            print(f"正在处理 {total_rows} 条 {level} 级别的事务数据...")
        
        # 将 "id1;id2;id3" 这样的字符串转换为 ['id1', 'id2', 'id3']
        # 使用 tqdm 显示进度（如果可用且数据量较大）
        if TQDM_AVAILABLE and total_rows > 1000:
            transactions = [row.split(';') for row in tqdm(df.iloc[:, 0], desc="处理事务数据", unit="事务")]
        else:
            transactions = [row.split(';') for row in df.iloc[:, 0]]
        
        logger.info(f"成功提取 {len(transactions)} 条 {level} 级别的事务数据。")
        return transactions

    def clear_cache(self):
        """清除DBManager的所有LRU缓存。"""
        self._execute_fetch_data_cached.cache_clear()
        logger.info("DBManager 缓存已清除。")
