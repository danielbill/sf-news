"""文本去重模块

实现三层去重策略：
1. 时间排重：只保留今天的文章
2. URL排重：与 today_news 中的 URL 对比
3. 标题近似排重：与 today_news 中的标题做 SimHash 对比
4. 批次内排重：本批次内的文章再互相做标题近似排重
"""

from datetime import date, datetime
from typing import List, Dict
from simhash import Simhash
import jieba
import threading

from ..models import Article
from ..storage import TimelineDB
from ..tools import TitleCleaner
from .url_cache import url_cache


class TodayNewsCache:
    """今日新闻缓存 - 存储 {url: title}，每天0点清空"""

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
        self._news: Dict[str, str] = {}  # {url: title}
        self._initialized = True

    def _check_and_reset(self):
        """检查日期，如果新的一天则清空缓存"""
        today = date.today()
        if self._cache_date != today:
            self._cache_date = today
            self._news.clear()
            print(f"[TodayNewsCache] 缓存已清零，新日期: {today}")

    def add(self, url: str, title: str):
        """添加新闻到缓存"""
        self._check_and_reset()
        self._news[url] = title

    def add_batch(self, articles: List[Article]):
        """批量添加新闻到缓存"""
        self._check_and_reset()
        for article in articles:
            self._news[article.url] = article.title

    def exists_url(self, url: str) -> bool:
        """检查 URL 是否已存在"""
        self._check_and_reset()
        return url in self._news

    def get_all_titles(self) -> List[str]:
        """获取所有缓存的标题"""
        self._check_and_reset()
        return list(self._news.values())

    def clear(self):
        """手动清空缓存"""
        self._news.clear()
        self._cache_date = date.today()

    @property
    def count(self) -> int:
        """获取当前缓存中的新闻数量"""
        self._check_and_reset()
        return len(self._news)

    @property
    def cache_date(self) -> date:
        """获取缓存对应的日期"""
        return self._cache_date


# 全局单例
today_news_cache = TodayNewsCache()


class TextDeduplicator:
    """文本去重器 - 四层去重策略"""

    # SimHash 汉明距离阈值（越大越宽松）
    # 对于20字的中文标题，汉明距离15表示前半部分相同
    SIMHASH_THRESHOLD = 15

    def __init__(self, target_date: date = None):
        """初始化去重器

        Args:
            target_date: 目标日期，默认为今天
        """
        self.target_date = target_date or date.today()
        self.db = TimelineDB(self.target_date)
        self.db.init_db()

    def dedup(self, articles: List[Article]) -> List[Article]:
        """执行四层去重

        Args:
            articles: 待去重的文章列表

        Returns:
            去重后的文章列表
        """
        print(f"[Dedup] 开始去重，原始文章数: {len(articles)}")
        print(f"[Dedup] url_cache.count={url_cache.count}, today_news_cache.count={today_news_cache.count}")

        # 第一层：时间排重 - 只保留今天的文章
        today_articles = self._filter_by_date(articles)
        print(f"[Dedup] 时间排重后: {len(today_articles)}")

        # 第二层：URL 排重 - 与 today_news_cache 对比 URL
        url_unique = self._filter_by_url(today_articles)
        print(f"[Dedup] URL排重后: {len(url_unique)}")

        # 第三层：标题近似排重 - 与 today_news_cache 中的标题对比
        title_unique = self._filter_by_cache_title(url_unique)
        print(f"[Dedup] 标题排重后: {len(title_unique)}")

        # 第四层：批次内排重 - 本批次内的文章互相做标题近似排重
        deduped = self._filter_by_batch_similarity(title_unique)
        print(f"[Dedup] 批次内排重后: {len(deduped)}")

        # 将最终留存的新闻添加到缓存
        today_news_cache.add_batch(deduped)

        return deduped

    def _filter_by_date(self, articles: List[Article]) -> List[Article]:
        """时间排重：只保留目标日期的文章"""
        result = []
        for a in articles:
            match = a.timestamp.date() == self.target_date
            if match:
                result.append(a)
            else:
                print(f"[Dedup] 时间过滤: {a.title[:30]}... | timestamp={a.timestamp}, target={self.target_date}")
        return result

    def _filter_by_url(self, articles: List[Article]) -> List[Article]:
        """URL 排重：与 today_news_cache 中的 URL 对比"""
        return [a for a in articles if not today_news_cache.exists_url(a.url)]

    def _filter_by_cache_title(self, articles: List[Article]) -> List[Article]:
        """标题近似排重：与 today_news_cache 中已有的标题对比"""
        # 获取缓存中所有标题的 SimHash
        cached_titles = today_news_cache.get_all_titles()
        if not cached_titles:
            return articles

        cached_hashes = [self._compute_simhash(t) for t in cached_titles]

        unique = []
        for article in articles:
            hash_value = self._compute_simhash(article.title)

            # 检查是否与缓存中的标题相似
            is_similar = False
            for cached_hash in cached_hashes:
                if hash_value.distance(cached_hash) <= self.SIMHASH_THRESHOLD:
                    is_similar = True
                    break

            if not is_similar:
                unique.append(article)

        return unique

    def _filter_by_batch_similarity(self, articles: List[Article]) -> List[Article]:
        """批次内排重：本批次内的文章互相做标题近似排重"""
        deduped = []

        for article in articles:
            hash_value = self._compute_simhash(article.title)

            # 检查是否与本次批次中已保留的标题相似
            is_similar = False
            for kept_article in deduped:
                kept_hash = self._compute_simhash(kept_article.title)
                if hash_value.distance(kept_hash) <= self.SIMHASH_THRESHOLD:
                    is_similar = True
                    break

            if not is_similar:
                deduped.append(article)

        return deduped

    def _compute_simhash(self, text: str) -> Simhash:
        """计算文本的 SimHash 值

        使用 jieba 分词提取关键词作为特征
        只取前20个字用于去重，只保留中英文数字
        """
        # 使用 TitleCleaner 清理标题（默认20个字）
        text = TitleCleaner.for_dedup(text)
        # 使用 jieba 分词
        words = list(jieba.cut(text))
        return Simhash(words)

    def get_stats(self, original_count: int, final_count: int) -> dict:
        """获取去重统计信息"""
        return {
            "original": original_count,
            "final": final_count,
            "removed": original_count - final_count,
            "rate": f"{(1 - final_count / original_count * 100) if original_count > 0 else 0:.1f}%"
        }
