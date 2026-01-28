"""调度器核心模块"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Dict, Any, Optional
from datetime import datetime

from ..config import ConfigReader
from .store import JobExecutionStore


class SchedulerManager:
    """调度器管理器

    负责管理定时抓取任务的调度、启动、停止、暂停等操作。

    约束：
    - 最小抓取间隔：15分钟（900秒）
    - 服务启动后默认立刻执行一次抓取
    """

    MIN_INTERVAL = 900  # 15分钟硬编码限制

    def __init__(self, config_dir: str = "config"):
        """初始化调度器

        Args:
            config_dir: 配置文件目录

        Raises:
            ValueError: 如果 interval 小于 MIN_INTERVAL
        """
        self.config_dir = config_dir
        self.config = self._load_config()

        # 验证最小间隔
        if self.config.interval < self.MIN_INTERVAL:
            raise ValueError(f"最小抓取间隔为 {self.MIN_INTERVAL} 秒")

        self.interval = self.config.interval
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.is_paused = False

        # 任务执行存储
        self.store = JobExecutionStore()

    def _load_config(self) -> Any:
        """加载配置"""
        reader = ConfigReader(self.config_dir)
        return reader.load_crawler_config().strategy

    async def start(self) -> None:
        """启动调度器

        启动时立即执行一次抓取，然后开始定时任务
        """
        if self.is_running:
            print("[Scheduler] 调度器已在运行")
            return

        print(f"[Scheduler] 启动调度器，间隔: {self.interval}秒")

        # 1. 立即执行一次抓取
        await self._run_crawl_job()

        # 2. 启动定时任务
        self.scheduler.add_job(
            self._run_crawl_job,
            'interval',
            seconds=self.interval,
            id='news_crawl',
            max_instances=1  # 防止任务重叠
        )
        self.scheduler.start()
        self.is_running = True
        self.is_paused = False

        print("[Scheduler] 调度器已启动")

    async def stop(self) -> None:
        """停止调度器"""
        if not self.is_running:
            print("[Scheduler] 调度器未运行")
            return

        print("[Scheduler] 停止调度器")
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        self.is_paused = False

    async def pause(self) -> None:
        """暂停调度器"""
        if not self.is_running or self.is_paused:
            print("[Scheduler] 调度器未运行或已暂停")
            return

        print("[Scheduler] 暂停调度器")
        self.scheduler.pause()
        self.is_paused = True

    async def resume(self) -> None:
        """恢复调度器"""
        if not self.is_running or not self.is_paused:
            print("[Scheduler] 调度器未运行或未暂停")
            return

        print("[Scheduler] 恢复调度器")
        self.scheduler.resume()
        self.is_paused = False

    @property
    def status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        job = self.scheduler.get_job('news_crawl') if self.is_running else None

        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "interval": self.interval,
            "next_run_time": job.next_run_time.isoformat() if job else None
        }

    async def _run_crawl_job(self) -> Dict[str, Any]:
        """执行抓取任务"""
        job_id = f"news_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[Scheduler] 执行任务: {job_id}")

        try:
            from ..api.crawl import run_crawl
            result = await run_crawl()

            # 记录执行结果
            self.store.record_execution(job_id, result)

            print(f"[Scheduler] 任务完成: 抓取 {result.get('total_saved', 0)} 条")
            return result

        except Exception as e:
            import traceback
            print(f"[Scheduler] 任务失败: {e}")
            traceback.print_exc()

            # 记录失败
            self.store.record_execution(job_id, {}, error=str(e))
            raise

    async def close(self) -> None:
        """关闭调度器"""
        await self.stop()
