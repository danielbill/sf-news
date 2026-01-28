"""任务执行记录存储"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class JobExecutionStore:
    """任务执行记录存储

    将每次抓取任务的执行结果存储到 SQLite 数据库
    """

    def __init__(self, db_path: str = None):
        """初始化存储

        Args:
            db_path: 数据库路径，默认从配置读取或使用默认值
        """
        if db_path is None:
            from ..config import ConfigReader
            reader = ConfigReader()
            config = reader.load_crawler_config()
            # 从 storage 配置读取，或使用默认值
            db_path = getattr(config.storage, 'db_path', 'data/db/scheduler.sqlite')

        self.db_path = db_path

    def _get_conn(self):
        """获取数据库连接"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        """初始化数据库"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                status TEXT NOT NULL,
                result_json TEXT,
                error_message TEXT,
                total_fetched INTEGER DEFAULT 0,
                after_dedup INTEGER DEFAULT 0,
                total_saved INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def record_execution(
        self,
        job_id: str,
        result: Dict[str, Any],
        error: Optional[str] = None
    ) -> int:
        """记录任务执行结果

        Args:
            job_id: 任务ID
            result: 执行结果字典
            error: 错误信息（如果失败）

        Returns:
            记录ID
        """
        self.init_db()

        conn = self._get_conn()
        cursor = conn.cursor()

        now = datetime.now()
        status = "failed" if error else "success"

        cursor.execute("""
            INSERT INTO job_executions (
                job_id, started_at, completed_at, status,
                result_json, error_message,
                total_fetched, after_dedup, total_saved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            now.isoformat(),
            now.isoformat(),
            status,
            json.dumps(result) if result else None,
            error,
            result.get("total_fetched", 0) if result else 0,
            result.get("after_dedup", 0) if result else 0,
            result.get("total_saved", 0) if result else 0,
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近执行记录

        Args:
            limit: 返回记录数量

        Returns:
            执行记录列表
        """
        self.init_db()

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, job_id, started_at, completed_at, status,
                   result_json, error_message,
                   total_fetched, after_dedup, total_saved
            FROM job_executions
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "job_id": row[1],
                "started_at": row[2],
                "completed_at": row[3],
                "status": row[4],
                "result": json.loads(row[5]) if row[5] else None,
                "error": row[6],
                "total_fetched": row[7],
                "after_dedup": row[8],
                "total_saved": row[9],
            }
            for row in rows
        ]

    def get_job_status(self) -> Dict[str, Any]:
        """获取任务统计状态

        Returns:
            统计信息字典
        """
        self.init_db()

        conn = self._get_conn()
        cursor = conn.cursor()

        # 总执行次数
        cursor.execute("SELECT COUNT(*) FROM job_executions")
        total_count = cursor.fetchone()[0]

        # 成功次数
        cursor.execute("SELECT COUNT(*) FROM job_executions WHERE status = 'success'")
        success_count = cursor.fetchone()[0]

        # 最后一次执行
        cursor.execute("""
            SELECT started_at, status, total_saved
            FROM job_executions
            ORDER BY started_at DESC
            LIMIT 1
        """)
        last_row = cursor.fetchone()

        conn.close()

        return {
            "total_executions": total_count,
            "success_count": success_count,
            "failure_count": total_count - success_count,
            "last_execution": {
                "started_at": last_row[0],
                "status": last_row[1],
                "total_saved": last_row[2]
            } if last_row else None
        }


# 类方法便捷接口（向后兼容）
def record_execution(job_id: str, result: Dict[str, Any], error: Optional[str] = None) -> int:
    """记录任务执行结果（便捷函数）"""
    return JobExecutionStore().record_execution(job_id, result, error)


def get_recent_jobs(limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近执行记录（便捷函数）"""
    return JobExecutionStore().get_recent_jobs(limit)
