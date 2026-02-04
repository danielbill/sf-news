"""Legend 数据库服务

管理 Legend 实体的 SQLite 数据库操作。
"""

import json
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.legend import (
    Legend,
    LegendCreate,
    LegendUpdate,
    LegendFilters,
    LegendType,
    LegendTier,
    ImpactLevel,
    LegendKeyword,
    LegendProduct,
    CompanyRelation,
    SyncLog,
    ProductCreate,
    CompanyRelationCreate,
)


class LegendDB:
    """Legend 数据库操作"""

    def __init__(self, db_path: str = "data/db/legend.sqlite"):
        self.db_path = Path(db_path)
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
            # legends 表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS legends (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name_en TEXT,
                    name_cn TEXT,
                    avatar_url TEXT,
                    legend_tier TEXT,
                    impact_level TEXT,
                    bio_short TEXT,
                    file_path TEXT,
                    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                    updated_at DATETIME DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_legends_type
                ON legends(type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_legends_tier
                ON legends(legend_tier)
            """)

            # legend_keywords 表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS legend_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    legend_id TEXT NOT NULL,
                    keyword_group TEXT,
                    keywords TEXT NOT NULL,
                    source_hash TEXT,
                    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                    updated_at DATETIME DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (legend_id) REFERENCES legends(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_legend_keywords_legend_id
                ON legend_keywords(legend_id)
            """)

            # legend_products 表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS legend_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    legend_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    category TEXT,
                    company_id TEXT,
                    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                    updated_at DATETIME DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (legend_id) REFERENCES legends(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_legend_products_legend_id
                ON legend_products(legend_id)
            """)

            # legend_companies 表（人物-公司关联）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS legend_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    role TEXT,
                    is_primary BOOLEAN DEFAULT 0,
                    start_date TEXT,
                    end_date TEXT,
                    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (person_id) REFERENCES legends(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES legends(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_legend_companies_person_id
                ON legend_companies(person_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_legend_companies_company_id
                ON legend_companies(company_id)
            """)

            # legend_sync_log 表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS legend_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT NOT NULL,
                    legend_id TEXT,
                    change_type TEXT,
                    details TEXT,
                    synced_at DATETIME DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_legend_sync_log_synced_at
                ON legend_sync_log(synced_at)
            """)

            conn.commit()

    # =========================================================================
    # Legend CRUD
    # =========================================================================

    def create_legend(self, legend: LegendCreate) -> str:
        """创建 Legend"""
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO legends (
                    id, type, name_en, name_cn, avatar_url,
                    legend_tier, impact_level, bio_short,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                legend.id,
                legend.type.value,
                legend.name_en,
                legend.name_cn,
                legend.avatar_url,
                legend.legend_tier.value,
                legend.impact_level.value,
                legend.bio_short,
                now,
                now
            ))
            conn.commit()
        return legend.id

    def get_legend(self, legend_id: str) -> Optional[Legend]:
        """获取单个 Legend"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM legends WHERE id = ?",
                (legend_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Legend(**dict(row))

    def list_legends(
        self,
        filters: Optional[LegendFilters] = None
    ) -> List[Legend]:
        """列出 Legends"""
        filters = filters or LegendFilters()

        with self.get_connection() as conn:
            where_conditions = []
            params = []

            if filters.type:
                where_conditions.append("type = ?")
                params.append(filters.type.value)

            if filters.tier:
                where_conditions.append("legend_tier = ?")
                params.append(filters.tier.value)

            if filters.impact_level:
                where_conditions.append("impact_level = ?")
                params.append(filters.impact_level.value)

            where_sql = ""
            if where_conditions:
                where_sql = "WHERE " + " AND ".join(where_conditions)

            params.extend([filters.limit, filters.offset])

            cursor = conn.execute(f"""
                SELECT * FROM legends
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, params)

            return [Legend(**dict(row)) for row in cursor.fetchall()]

    def update_legend(self, legend_id: str, data: LegendUpdate) -> bool:
        """更新 Legend"""
        updates = []
        params = []

        if data.name_en is not None:
            updates.append("name_en = ?")
            params.append(data.name_en)
        if data.name_cn is not None:
            updates.append("name_cn = ?")
            params.append(data.name_cn)
        if data.avatar_url is not None:
            updates.append("avatar_url = ?")
            params.append(data.avatar_url)
        if data.bio_short is not None:
            updates.append("bio_short = ?")
            params.append(data.bio_short)
        if data.legend_tier is not None:
            updates.append("legend_tier = ?")
            params.append(data.legend_tier.value)
        if data.impact_level is not None:
            updates.append("impact_level = ?")
            params.append(data.impact_level.value)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(legend_id)

        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE legends
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_legend(self, legend_id: str) -> bool:
        """删除 Legend（软删除/归档）"""
        # 简单实现：直接删除，后续可改为软删除
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM legends WHERE id = ?",
                (legend_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def legend_exists(self, legend_id: str) -> bool:
        """检查 Legend 是否存在"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM legends WHERE id = ?",
                (legend_id,)
            )
            return cursor.fetchone() is not None

    # =========================================================================
    # Keywords
    # =========================================================================

    def set_keywords(
        self,
        legend_id: str,
        keywords: List[Dict[str, Any]],
        source_hash: Optional[str] = None
    ) -> None:
        """设置 Legend 的关键词（替换全部）"""
        with self.get_connection() as conn:
            # 先删除旧的关键词
            conn.execute(
                "DELETE FROM legend_keywords WHERE legend_id = ?",
                (legend_id,)
            )

            # 插入新的关键词
            now = datetime.now().isoformat()
            for kw_group in keywords:
                conn.execute("""
                    INSERT INTO legend_keywords (
                        legend_id, keyword_group, keywords, source_hash,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    legend_id,
                    kw_group.get("group_name"),
                    json.dumps(kw_group["keywords"], ensure_ascii=False),
                    source_hash,
                    now,
                    now
                ))
            conn.commit()

    def get_keywords(self, legend_id: str) -> List[LegendKeyword]:
        """获取 Legend 的所有关键词"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM legend_keywords
                WHERE legend_id = ?
                ORDER BY id
            """, (legend_id,))

            result = []
            for row in cursor.fetchall():
                data = dict(row)
                # 解析 JSON
                data["keywords"] = json.loads(data["keywords"])
                result.append(LegendKeyword(**data))
            return result

    def keywords_changed(
        self,
        legend_id: str,
        new_keywords_flat: List[str],
        new_hash: str
    ) -> bool:
        """检查关键词是否变化

        Args:
            legend_id: Legend ID
            new_keywords_flat: 新的关键词（展平后）
            new_hash: 新的关键词哈希值

        Returns:
            True 表示有变化
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT source_hash FROM legend_keywords
                WHERE legend_id = ?
                LIMIT 1
            """, (legend_id,))
            row = cursor.fetchone()

            if not row:
                return True  # 从未有关键词，视为变化

            old_hash = row["source_hash"]
            return old_hash != new_hash

    # =========================================================================
    # Products
    # =========================================================================

    def add_product(self, product: ProductCreate) -> int:
        """添加产品"""
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO legend_products (
                    legend_id, product_name, description, status,
                    category, company_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.legend_id,
                product.product_name,
                product.description,
                product.status.value,
                product.category,
                product.company_id,
                now,
                now
            ))
            conn.commit()
            return cursor.lastrowid

    def list_products(self, legend_id: str) -> List[LegendProduct]:
        """获取 Legend 的产品列表"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM legend_products
                WHERE legend_id = ?
                ORDER BY id
            """, (legend_id,))

            return [LegendProduct(**dict(row)) for row in cursor.fetchall()]

    # =========================================================================
    # Companies (人物-公司关联)
    # =========================================================================

    def add_company_relation(self, relation: CompanyRelationCreate) -> int:
        """添加人物-公司关联"""
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO legend_companies (
                    person_id, company_id, role, is_primary,
                    start_date, end_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                relation.person_id,
                relation.company_id,
                relation.role,
                1 if relation.is_primary else 0,
                relation.start_date,
                relation.end_date,
                now
            ))
            conn.commit()
            return cursor.lastrowid

    def list_person_companies(self, person_id: str) -> List[CompanyRelation]:
        """获取人物关联的公司列表"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM legend_companies
                WHERE person_id = ?
                ORDER BY is_primary DESC, id
            """, (person_id,))

            # 转换 is_primary 为布尔值
            result = []
            for row in cursor.fetchall():
                data = dict(row)
                data["is_primary"] = bool(data["is_primary"])
                result.append(CompanyRelation(**data))
            return result

    def list_company_people(self, company_id: str) -> List[CompanyRelation]:
        """获取公司关联的人物列表"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM legend_companies
                WHERE company_id = ?
                ORDER BY is_primary DESC, id
            """, (company_id,))

            result = []
            for row in cursor.fetchall():
                data = dict(row)
                data["is_primary"] = bool(data["is_primary"])
                result.append(CompanyRelation(**data))
            return result

    # =========================================================================
    # Sync Log
    # =========================================================================

    def log_sync(
        self,
        sync_type: str,
        legend_id: Optional[str] = None,
        change_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录同步日志"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO legend_sync_log (
                    sync_type, legend_id, change_type, details
                ) VALUES (?, ?, ?, ?)
            """, (
                sync_type,
                legend_id,
                change_type,
                json.dumps(details, ensure_ascii=False) if details else None
            ))
            conn.commit()

    def get_sync_logs(self, limit: int = 50) -> List[SyncLog]:
        """获取同步日志"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM legend_sync_log
                ORDER BY synced_at DESC
                LIMIT ?
            """, (limit,))

            result = []
            for row in cursor.fetchall():
                data = dict(row)
                if data["details"]:
                    data["details"] = json.loads(data["details"])
                result.append(SyncLog(**data))
            return result

    # =========================================================================
    # 批量操作
    # =========================================================================

    def get_all_legend_ids(self) -> List[str]:
        """获取所有 Legend ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id FROM legends")
            return [row["id"] for row in cursor.fetchall()]

    def get_file_hash(self, legend_id: str) -> Optional[str]:
        """获取存储的关键词哈希值"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT source_hash FROM legend_keywords
                WHERE legend_id = ?
                LIMIT 1
            """, (legend_id,))
            row = cursor.fetchone()
            return row["source_hash"] if row else None
