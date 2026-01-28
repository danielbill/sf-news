"""爬虫模块"""

from .base import BaseCrawler
from .cankaoxiaoxi import CankaoxiaoxiCrawler
from .universal import UniversalCrawler
from .dedup import TextDeduplicator
from .url_cache import url_cache

__all__ = [
    "BaseCrawler",
    "CankaoxiaoxiCrawler",
    "UniversalCrawler",
    "TextDeduplicator",
    "url_cache",
]
