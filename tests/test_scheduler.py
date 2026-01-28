"""调度器测试"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import date

from src.scheduler import SchedulerManager, JobExecutionStore
from src.config import ConfigReader


@pytest.fixture
def temp_config_dir():
    """临时配置目录"""
    temp_dir = tempfile.mkdtemp()
    config_file = Path(temp_dir) / "crawler_config.yaml"

    # 写入测试配置
    config_file.write_text("""
strategy:
  interval: 900
  min_interval: 900
  concurrent: 3

network:
  timeout: 30
  retry: 3
  retry_delay: 5
  user_agent: "Test"

storage:
  save_content: true
  dedup: true
  content_format: "markdown"
  db_path: "data/db/scheduler.sqlite"

logging:
  level: "INFO"
  save_logs: true
  log_dir: "logs"
""")

    yield temp_dir

    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db():
    """临时数据库"""
    temp_file = tempfile.mktemp(suffix=".sqlite")
    yield temp_file
    Path(temp_file).unlink(missing_ok=True)


class TestSchedulerManager:
    """测试 SchedulerManager"""

    def test_init_with_valid_interval(self, temp_config_dir):
        """测试初始化 - 有效间隔"""
        scheduler = SchedulerManager(config_dir=temp_config_dir)
        assert scheduler.interval == 900
        assert scheduler.is_running is False
        assert scheduler.is_paused is False

    def test_init_with_invalid_interval(self, temp_config_dir):
        """测试初始化 - 无效间隔（小于最小值）"""
        # 修改配置文件使 interval < min_interval
        config_file = Path(temp_config_dir) / "crawler_config.yaml"
        config = config_file.read_text()
        config = config.replace("interval: 900", "interval: 300")
        config_file.write_text(config)

        with pytest.raises(ValueError, match="最小抓取间隔"):
            SchedulerManager(config_dir=temp_config_dir)

    def test_status_property(self, temp_config_dir):
        """测试状态属性"""
        scheduler = SchedulerManager(config_dir=temp_config_dir)
        status = scheduler.status

        assert status["is_running"] is False
        assert status["is_paused"] is False
        assert status["interval"] == 900
        assert status["next_run_time"] is None


class TestJobExecutionStore:
    """测试 JobExecutionStore"""

    def test_init_with_default_db(self):
        """测试初始化 - 默认数据库路径"""
        store = JobExecutionStore()
        assert store.db_path.endswith("scheduler.sqlite")

    def test_init_with_custom_db(self, temp_db):
        """测试初始化 - 自定义数据库路径"""
        store = JobExecutionStore(db_path=temp_db)
        assert store.db_path == temp_db

    def test_init_db(self, temp_db):
        """测试数据库初始化"""
        store = JobExecutionStore(db_path=temp_db)
        store.init_db()

        # 验证表已创建
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='job_executions'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_record_execution_success(self, temp_db):
        """测试记录成功执行"""
        store = JobExecutionStore(db_path=temp_db)
        result = {
            "total_fetched": 10,
            "after_dedup": 8,
            "total_saved": 5
        }

        record_id = store.record_execution("test_job_001", result)

        assert record_id > 0

        # 验证记录内容
        jobs = store.get_recent_jobs(limit=1)
        assert len(jobs) == 1
        assert jobs[0]["job_id"] == "test_job_001"
        assert jobs[0]["status"] == "success"
        assert jobs[0]["total_fetched"] == 10
        assert jobs[0]["total_saved"] == 5

    def test_record_execution_failure(self, temp_db):
        """测试记录失败执行"""
        store = JobExecutionStore(db_path=temp_db)

        record_id = store.record_execution(
            "test_job_002",
            {},
            error="Connection timeout"
        )

        assert record_id > 0

        # 验证记录内容
        jobs = store.get_recent_jobs(limit=1)
        assert len(jobs) == 1
        assert jobs[0]["status"] == "failed"
        assert jobs[0]["error"] == "Connection timeout"

    def test_get_recent_jobs(self, temp_db):
        """测试获取最近执行记录"""
        store = JobExecutionStore(db_path=temp_db)

        # 创建多条记录
        for i in range(5):
            store.record_execution(
                f"job_{i:03d}",
                {"total_saved": i}
            )

        # 获取最近3条
        jobs = store.get_recent_jobs(limit=3)
        assert len(jobs) == 3

    def test_get_job_status(self, temp_db):
        """测试获取任务统计"""
        store = JobExecutionStore(db_path=temp_db)

        # 添加成功和失败的记录
        store.record_execution("job_001", {"total_saved": 10})
        store.record_execution("job_002", {}, error="Error")
        store.record_execution("job_003", {"total_saved": 20})

        status = store.get_job_status()

        assert status["total_executions"] == 3
        assert status["success_count"] == 2
        assert status["failure_count"] == 1
        assert status["last_execution"]["total_saved"] == 20
