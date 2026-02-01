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
                # 检查列名，进行迁移
                cursor = conn.execute("PRAGMA table_info(articles)")
                columns = {row["name"] for row in cursor.fetchall()}

                # 迁移：添加 legend 列
                if "legend" not in columns:
                    conn.execute("ALTER TABLE articles ADD COLUMN legend TEXT")
                    print("[DB] 已添加 legend 列到现有表")

                # 迁移：timestamp -> publish_time
                if "timestamp" in columns and "publish_time" not in columns:
                    self._migrate_timestamp_to_publish_time(conn)
            else:
                # 创建新表（使用 publish_time）
                conn.execute("""
                    CREATE TABLE articles (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE,
                        source TEXT NOT NULL,
                        publish_time DATETIME NOT NULL,
                        file_path TEXT,
                        tags TEXT,
                        entities TEXT,
                        legend TEXT,
                        created_at DATETIME DEFAULT (datetime('now', 'localtime'))
                    )
                """)
                print("[DB] 已创建新表")

            # 创建索引（兼容旧列名和新列名）
            for column in ["publish_time", "timestamp"]:
                try:
                    conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_articles_{column}
                        ON articles({column})
                    """)
                except sqlite3.OperationalError:
                    pass  # 列不存在，跳过

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_source
                ON articles(source)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_legend
                ON articles(legend)
            """)
            conn.commit()

    def _migrate_timestamp_to_publish_time(self, conn) -> None:
        """迁移 timestamp 列为 publish_time

        SQLite 不支持直接重命名列，需要重建表
        """
        print("[DB] 开始迁移 timestamp -> publish_time")

        # 1. 创建新表
        conn.execute("""
            CREATE TABLE articles_new (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT UNIQUE,
                source TEXT NOT NULL,
                publish_time DATETIME NOT NULL,
                file_path TEXT,
                tags TEXT,
                entities TEXT,
                legend TEXT,
                created_at DATETIME DEFAULT (datetime('now', 'localtime'))
            )
        """)

        # 2. 复制数据
        conn.execute("""
            INSERT INTO articles_new (id, title, url, source, publish_time, file_path, tags, entities, legend, created_at)
            SELECT id, title, url, source, timestamp, file_path, tags, entities, legend, created_at
            FROM articles
        """)

        # 3. 删除旧表
        conn.execute("DROP TABLE articles")

        # 4. 重命名新表
        conn.execute("ALTER TABLE articles_new RENAME TO articles")

        print(f"[DB] 已迁移 {conn.total_changes} 条记录 timestamp -> publish_time")

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

        # 处理 publish_time - 必须从 article.publish_time 获取
        publish_time_value = article.publish_time
        if hasattr(publish_time_value, 'isoformat'):
            publish_time_value = publish_time_value.isoformat()
        else:
            publish_time_value = str(publish_time_value)

        with self.get_connection() as conn:
            # 优先使用 publish_time，回退到 timestamp（兼容旧数据）
            column_name = "publish_time"
            try:
                conn.execute(f"""
                    INSERT OR REPLACE INTO articles
                    (id, title, url, source, {column_name}, file_path, tags, entities, legend, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.id,
                    article.title,
                    article.url,
                    source_value,
                    publish_time_value,
                    article.file_path,
                    json.dumps(article.tags) if article.tags else None,
                    json.dumps(article.entities) if article.entities else None,
                    article.legend,
                    created_at
                ))
            except sqlite3.OperationalError:
                # 回退到 timestamp（旧数据库）
                conn.execute("""
                    INSERT OR REPLACE INTO articles
                    (id, title, url, source, timestamp, file_path, tags, entities, legend, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.id,
                    article.title,
                    article.url,
                    source_value,
                    publish_time_value,
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
            # 检测使用哪个列名
            time_column = self._get_time_column(conn)

            # 构建 WHERE 条件
            where_conditions = []
            params = []

            if start_date:
                where_conditions.append(f"date({time_column}) >= date(?)")
                params.append(start_date)

            if end_date:
                where_conditions.append(f"date({time_column}) <= date(?)")
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
                    ORDER BY {time_column} DESC
                    LIMIT ? OFFSET ?
                """
            else:
                sql = f"""
                    SELECT * FROM articles
                    ORDER BY {time_column} DESC
                    LIMIT ? OFFSET ?
                """
                params = [limit, offset]

            cursor = conn.execute(sql, params)
            return [self._normalize_article(dict(row)) for row in cursor.fetchall()]

    def list_articles_latest(self, limit: int = 100, legend: str = None) -> List[dict]:
        """获取最新新闻（不限日期）

        Args:
            limit: 返回条数
            legend: 筛选传奇人物（可选）
        """
        with self.get_connection() as conn:
            time_column = self._get_time_column(conn)

            if legend:
                cursor = conn.execute(f"""
                    SELECT * FROM articles
                    WHERE legend = ?
                    ORDER BY {time_column} DESC
                    LIMIT ?
                """, (legend, limit))
            else:
                cursor = conn.execute(f"""
                    SELECT * FROM articles
                    ORDER BY {time_column} DESC
                    LIMIT ?
                """, (limit,))
            return [self._normalize_article(dict(row)) for row in cursor.fetchall()]

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
        where_conditions = [f"date({TimelineDB._detect_time_column_for_db(db_dir / f'timeline_{query_years[0]}.sqlite')}) >= date(?)"]
        params = [start_date]

        if end_date:
            where_conditions.append(f"date({TimelineDB._detect_time_column_for_db(db_dir / f'timeline_{query_years[0]}.sqlite')}) <= date(?)")
            params.append(end_date)

        if legend:
            where_conditions.append("legend = ?")
            params.append(legend)

        params.append(limit * 2)

        where_sql = " AND ".join(where_conditions)
        sql = f"""
            SELECT * FROM articles
            WHERE {where_sql}
            ORDER BY {TimelineDB._detect_time_column_for_db(db_dir / f'timeline_{query_years[0]}.sqlite')} DESC
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
        if all_articles:
            time_key = 'publish_time' if 'publish_time' in all_articles[0] else 'timestamp'
        else:
            time_key = 'timestamp'
        all_articles.sort(key=lambda x: x[time_key], reverse=True)
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

    def _get_time_column(self, conn) -> str:
        """获取时间列名（兼容新旧数据库）"""
        cursor = conn.execute("PRAGMA table_info(articles)")
        columns = {row["name"] for row in cursor.fetchall()}
        return "publish_time" if "publish_time" in columns else "timestamp"

    @staticmethod
    def _detect_time_column_for_db(db_path: Path) -> str:
        """检测指定数据库使用的时间列名"""
        if not db_path.exists():
            return "timestamp"  # 默认旧列名
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("PRAGMA table_info(articles)")
            columns = {row["name"] for row in cursor.fetchall()}
            conn.close()
            return "publish_time" if "publish_time" in columns else "timestamp"
        except Exception:
            return "timestamp"

    def _normalize_article(self, article: dict) -> dict:
        """标准化文章数据（兼容新旧列名）"""
        # 同时兼容 publish_time 和 timestamp
        if "publish_time" not in article and "timestamp" in article:
            article["publish_time"] = article["timestamp"]
        elif "timestamp" not in article and "publish_time" in article:
            article["timestamp"] = article["publish_time"]
        return article
