"""内存 URL 缓存模块

用于快速去重，每日 0 点清零。

功能：
1. 存储当日所有已处理的 URL
2. 提供 O(1) 查询复杂度的去重检查
3. 每日自动清零
"""

from datetime import date, datetime
from typing import Set
import threading


class URLCache:
    """内存 URL 缓存 - 每日清零"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化缓存"""
        if self._initialized:
            return

        self._cache_date: date = date.today()
        self._urls: Set[str] = set()
        self._initialized = True

    def _check_and_reset(self):
        """检查日期，如果新的一天则清空缓存"""
        today = date.today()
        if self._cache_date != today:
            self._cache_date = today
            self._urls.clear()
            print(f"[URLCache] 缓存已清零，新日期: {today}")

    def add(self, url: str):
        """添加 URL 到缓存

        Args:
            url: 要添加的 URL
        """
        self._check_and_reset()
        self._urls.add(url)

    def add_batch(self, urls: list[str]):
        """批量添加 URL 到缓存

        Args:
            urls: 要添加的 URL 列表
        """
        self._check_and_reset()
        self._urls.update(urls)

    def exists(self, url: str) -> bool:
        """检查 URL 是否已存在

        Args:
            url: 要检查的 URL

        Returns:
            True 如果 URL 已存在，False 否则
        """
        self._check_and_reset()
        return url in self._urls

    def clear(self):
        """手动清空缓存"""
        self._urls.clear()
        self._cache_date = date.today()

    @property
    def count(self) -> int:
        """获取当前缓存中的 URL 数量"""
        self._check_and_reset()
        return len(self._urls)

    @property
    def cache_date(self) -> date:
        """获取缓存对应的日期"""
        return self._cache_date

    def get_all_urls(self) -> Set[str]:
        """获取所有缓存的 URL"""
        self._check_and_reset()
        return self._urls.copy()


# 全局单例
url_cache = URLCache()
