"""存储模块"""

from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List
import sqlite3
from contextlib import contextmanager

from ..models import Article


class TimelineDB:
    """Timeline 数据库管理（一年一个 DB）"""

    def __init__(self, db_date: Optional[date] = None):
        self.db_date = db_date or date.today()
        # 按年分库：timeline_2025.sqlite
        self.db_path = Path(f"data/db/timeline_{self.db_date.strftime('%Y')}.sqlite")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            # 检查表是否存在
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='articles'
            """)
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # 检查是否有 legend 列
                cursor = conn.execute("PRAGMA table_info(articles)")
                columns = {row["name"] for row in cursor.fetchall()}
                if "legend" not in columns:
                    # 添加 legend 列（迁移旧数据库）
                    conn.execute("ALTER TABLE articles ADD COLUMN legend TEXT")
                    print("[DB] 已添加 legend 列到现有表")
            else:
                # 创建新表
                conn.execute("""
                    CREATE TABLE articles (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE,
                        source TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        file_path TEXT,
                        tags TEXT,
                        entities TEXT,
                        legend TEXT,
                        created_at DATETIME DEFAULT (datetime('now', 'localtime'))
                    )
                """)
                print("[DB] 已创建新表")

            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_timestamp
                ON articles(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_source
                ON articles(source)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_legend
                ON articles(legend)
            """)
            conn.commit()

    def insert_article(self, article: Article) -> None:
        """插入文章"""
        import json

        # 获取北京时间
        beijing_tz = timezone(timedelta(hours=8))
        created_at = datetime.now(beijing_tz).isoformat()

        # 处理 source - 可能是枚举或字符串
        source_value = article.source
        if hasattr(article.source, 'value'):
            source_value = article.source.value
        elif isinstance(article.source, str):
            source_value = article.source

        # 处理 timestamp - 可能是 datetime 或 date
        timestamp_value = article.timestamp
        if hasattr(timestamp_value, 'isoformat'):
            timestamp_value = timestamp_value.isoformat()
        else:
            timestamp_value = str(timestamp_value)

        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO articles
                (id, title, url, source, timestamp, file_path, tags, entities, legend, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.id,
                article.title,
                article.url,
                source_value,
                timestamp_value,
                article.file_path,
                json.dumps(article.tags) if article.tags else None,
                json.dumps(article.entities) if article.entities else None,
                article.legend,
                created_at
            ))
            conn.commit()

    def get_article(self, article_id: str) -> Optional[dict]:
        """获取单篇文章"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM articles WHERE id = ?",
                (article_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_articles(self, limit: int = 100, offset: int = 0, legend: str = None,
                      start_date: str = None, end_date: str = None) -> List[dict]:
        """列出文章

        Args:
            limit: 返回条数
            offset: 偏移量
            legend: 筛选传奇人物（可选）
            start_date: 开始日期 YYYY-MM-DD（可选）
            end_date: 结束日期 YYYY-MM-DD（可选）
        """
        with self.get_connection() as conn:
            # 构建 WHERE 条件
            where_conditions = []
            params = []

            if start_date:
                where_conditions.append("date(timestamp) >= date(?)")
                params.append(start_date)

            if end_date:
                where_conditions.append("date(timestamp) <= date(?)")
                params.append(end_date)

            if legend:
                where_conditions.append("legend = ?")
                params.append(legend)

            # 如果没有条件，返回所有
            if where_conditions:
                where_sql = " AND ".join(where_conditions)
                params.extend([limit, offset])
                sql = f"""
                    SELECT * FROM articles
                    WHERE {where_sql}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """
            else:
                sql = """
                    SELECT * FROM articles
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """
                params = [limit, offset]

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def list_articles_latest(self, limit: int = 100, legend: str = None) -> List[dict]:
        """获取最新新闻（不限日期）

        Args:
            limit: 返回条数
            legend: 筛选传奇人物（可选）
        """
        with self.get_connection() as conn:
            if legend:
                cursor = conn.execute("""
                    SELECT * FROM articles
                    WHERE legend = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (legend, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM articles
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def list_articles_multi_year(years: int = 2, limit: int = 100, legend: str = None,
                                start_date: str = None, end_date: str = None) -> List[dict]:
        """列出多年文章（跨库查询）

        Args:
            years: 查询最近几年
            limit: 总共返回多少条
            legend: 筛选传奇人物（可选）
            start_date: 开始日期 YYYY-MM-DD（可选，默认今日）
            end_date: 结束日期 YYYY-MM-DD（可选）

        Returns:
            文章列表，按时间倒序
        """
        from datetime import date

        all_articles = []
        db_dir = Path("data/db")

        # 默认查询今日及以后
        if not start_date:
            start_date = date.today().isoformat()

        # 收集要查询的年份
        current_year = date.today().year
        query_years = []
        for i in range(years):
            year = current_year - i
            db_path = db_dir / f"timeline_{year}.sqlite"
            if db_path.exists():
                query_years.append(year)

        # 构建 WHERE 条件
        where_conditions = ["date(timestamp) >= date(?)"]
        params = [start_date]

        if end_date:
            where_conditions.append("date(timestamp) <= date(?)")
            params.append(end_date)

        if legend:
            where_conditions.append("legend = ?")
            params.append(legend)

        params.append(limit * 2)

        where_sql = " AND ".join(where_conditions)
        sql = f"""
            SELECT * FROM articles
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?
        """

        # 从每个数据库读取
        for year in query_years:
            temp_date = date(year, 1, 1)
            db = TimelineDB(temp_date)
            with db.get_connection() as conn:
                cursor = conn.execute(sql, params)
                articles = [dict(row) for row in cursor.fetchall()]
                all_articles.extend(articles)

        # 按时间排序并限制数量
        all_articles.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_articles[:limit]

    def article_exists(self, url: str) -> bool:
        """检查文章是否已存在"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM articles WHERE url = ?",
                (url,)
            )
            return cursor.fetchone() is not None

    def clear_all(self) -> int:
        """清空所有文章数据

        Returns:
            删除的行数
        """
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM articles")
            conn.commit()
            return cursor.rowcount
